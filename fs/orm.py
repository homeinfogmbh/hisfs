"""ORM models"""

from os.path import normpath
from contextlib import suppress

from peewee import DoesNotExist, ForeignKeyField, IntegerField, CharField

from homeinfo.crm import Customer
from homeinfo.lib.fs import FileMode
from filedb import FileError, FileClient

from his.orm import module_model, Account
from .errors import NotADirectory, NotAFile, NoSuchNode, ReadError, \
    WriteError, DirectoryNotEmpty

__all__ = [
    'FileNotFound',
    'ConsistencyError',
    'Inode']


class FileNotFound(Exception):
    """Indicates that the respective file was not found"""

    def __init__(self, path):
        super().__init__(path)
        self.path = path


class ConsistencyError(Exception):
    """Indicates that the consistency of
    the file system has been compromised
    """

    def __init__(self, inode):
        super().__init__(inode)
        self.inode = inode


def root(inodes):
    """Yields inodes that are root directories"""

    for inode in inodes:
        if inode.isdir and inode.root:
            yield inode


class Inode(module_model('fs')):
    """Inode database model for the virtual filesystem"""

    PATHSEP = '/'
    FILE_CLIENT = FileClient('7958faef-01c9-4c3b-b4ef-1aecea6945c1')

    parent = ForeignKeyField('self', db_column='parent', null=True)
    _name = CharField(255, db_column='name')
    owner = ForeignKeyField(Account, db_column='owner')
    group = ForeignKeyField(Customer, db_column='group')
    _mode = IntegerField(db_column='mode')  # SMALLINT field!
    file = IntegerField(null=True, default=None)

    @classmethod
    def by_owner(cls, owner):
        """Yields inodes of the respective owner"""
        return cls.select().where(cls.owner == owner)

    @classmethod
    def by_group(cls, group):
        """Yieds inodes of the respective group"""
        return cls.select().where(cls.group == group)

    @classmethod
    def by_ownership(cls, owner, group):
        """Yields inodes that are owned by
        the respective owner and group
        """
        for inode in cls.by_owner:
            if inode.group == group:
                yield inode

    @classmethod
    def from_path(cls, path, customer):
        """Returns the INode handler from the respective path"""
        parent = cls.root_for(group=customer)
        processed_path = ['']

        for inode in path.split(cls.PATHSEP):
            if not inode:
                continue
            else:
                processed_path.append(inode)

                try:
                    parent = cls.get(
                        (cls.group == customer) &
                        (cls.parent == parent) &
                        (cls.name == inode))
                except DoesNotExist:
                    raise FileNotFound(cls.PATHSEP.join(processed_path))

        return parent

    @classmethod
    def by_sha256(cls, sha256sum, customer):
        """Returns INodes by SHA-256 checksum match"""
        for inode in cls.by_group(customer):
            if inode.sha256sum == sha256sum:
                yield inode

    @classmethod
    def getrel(cls, name, parent, owner, group):
        """Get inode by relative properties."""
        if parent is None:
            return cls.get(
                (cls._name == name) &
                (cls.parent >> None) &
                (cls.owner == owner) &
                (cls.group == group))
        else:
            return cls.get(
                (cls._name == name) &
                (cls.parent == parent) &
                (cls.owner == owner) &
                (cls.group == group))

    @classmethod
    def root_for(cls, owner=None, group=None):
        """Yields elements of the respective root folder"""
        if owner is None and group is None:
            return cls.get(
                (cls.file >> None) &
                (cls.parent >> None))
        elif owner is not None and group is None:
            return cls.get(
                (cls.file >> None) &
                (cls.parent >> None) &
                (cls.owner == owner))
        elif owner is None and group is not None:
            return cls.get(
                (cls.file >> None) &
                (cls.parent >> None) &
                (cls.group == group))
        else:
            return cls.get(
                (cls.file >> None) &
                (cls.parent >> None) &
                (cls.owner == owner) &
                (cls.group == group))

    @classmethod
    def _node_path(cls, revpath, owner=None, group=None):
        """Finds records by reversed path nodes"""
        parent = cls.root_for(owner=owner, group=group)
        path = [parent]

        while revpath:
            node = revpath.pop()

            try:
                parent = cls.getrel(node, parent, owner, group)
            except DoesNotExist:
                raise NoSuchNode() from None
            else:
                # Bail out if the node is a file
                # but is expected to have children.
                if parent.isfile and revpath:
                    raise NotADirectory() from None
                else:
                    path.append(parent)

        return path

    @classmethod
    def node_path(cls, path, owner=None, group=None):
        """Yields files and directories by the respective path"""
        if not path:
            revpath = []
        else:
            normed_path = normpath(path)

            if normed_path == cls.PATHSEP:
                revpath = []
            else:
                revpath = list(reversed(normed_path.split(cls.PATHSEP)))

        return cls._node_path(revpath, owner=owner, group=group)

    @property
    def name(self):
        """Returns the inode's name"""
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name"""
        if not name:
            raise ValueError('File name must not be empty.')
        elif self.PATHSEP in name:
            raise ValueError('File name must not contain "{}".'.format(
                self.PATHSEP))
        else:
            self._name = name

    @property
    def mode(self):
        """Returns the file mode"""
        return FileMode(self._mode)

    @mode.setter
    def mode(self, mode):
        """Sets the file mode"""
        self._mode = int(mode)

    @property
    def revpath(self):
        """Returns the reversed path nodes towards the inode"""
        yield self.name
        parent = self.parent

        while parent is not None:
            yield parent.name
            parent = parent.parent

        yield ''    # Root directory

    @property
    def path(self):
        """Returns the path to the inode"""
        return self.PATHSEP.join(reversed(self.revpath))

    @property
    def root(self):
        """Determines whether the inode is on the root level"""
        return self.parent is None

    @property
    def isdir(self):
        """Determines whether the inode is a directory"""
        return self.file is None

    @property
    def isfile(self):
        """Determines whether the inode is a file"""
        return not self.isdir

    @property
    def data(self):
        """Returns the file's content"""
        if self.file is None:
            raise NotAFile()
        else:
            try:
                return self.FILE_CLIENT.get(self.file)
            except FileError:
                raise ReadError()

    @data.setter
    def data(self, data):
        """Returns the file's content"""
        if self.file is None and self.id is not None:
            raise NotAFile()
        else:
            try:
                file_id = self.FILE_CLIENT.add(data)
            except FileError:
                raise WriteError()
            else:
                with suppress(FileError):
                    self.FILE_CLIENT.delete(self.file)

                self.file = file_id

    @property
    def sha256sum(self):
        """Returns the expected SHA-256 checksum"""
        if self.file is None:
            raise NotAFile()
        else:
            try:
                return self.FILE_CLIENT.sha256sum(self.file)
            except FileError:
                raise ReadError() from None

    @property
    def mimetype(self):
        """Returns the MIME type"""
        if self.file is None:
            raise NotAFile()
        else:
            try:
                return self.FILE_CLIENT.mimetype(self.file)
            except FileError:
                raise ReadError() from None

    @property
    def size(self):
        """Returns the size in bytes"""
        if self.file is None:
            raise NotAFile()
        else:
            try:
                return self.FILE_CLIENT.size(self.file)
            except FileError:
                raise ReadError() from None

    @property
    def children(self):
        """Yields the directoie's children"""
        if self.isdir:
            return self.__class__.select().where(self.__class__.parent == self)
        else:
            raise NotADirectory()

    def remove(self, recursive=False):
        """Removes a virtual inode"""
        if recursive:
            for child in self.__class__.select().where(
                    self.__class__.parent == self):
                child.remove(recursive=True)

        self.unlink()

    def unlink(self):
        """Deletes a virtual inode"""
        try:
            self.__class__.get(self.__class__.parent == self)
        except DoesNotExist:
            pass
        else:
            raise DirectoryNotEmpty()

        if self.file is not None:
            self.FILE_CLIENT.delete(self.file)

        self.delete_instance()

    def to_dict(self, children=True, mimetype=True, size=True):
        """Converts the inode into a dictionary"""
        result = {
            'name': self.name,
            'owner': repr(self.owner),
            'group': repr(self.group),
            'mode': str(self.mode)}

        if self.isdir:
            if children:
                result['children'] = [c.name for c in self.children]
        else:
            if mimetype:
                result['mimetype'] = self.mimetype

            if size:
                result['size'] = self.size

        return result

    def dict_for(self, account):
        """Converts the inode into a dictionary
        considering access permissions
        """
        if (self.parent or self).executable_by(account):
            fs_dict = self.to_dict(children=False)

            if self.isdir:
                fs_dict['children'] = [
                    c.to_dict(account) for c in self.children]

            return fs_dict
        else:
            return {}

    def _readable_by(self, account):
        """Determines whether this inode is
        readable by a certain account
        """
        mode = self.mode

        if account.root:
            return True
        elif mode.user.read and account == self.owner:
            return True
        elif mode.group.read and account.customer == self.owner.customer:
            return True
        elif mode.other.read:
            return True
        else:
            return False

    def _writable_by(self, account):
        """Determines whether this inode is
        writable by a certain account
        """
        mode = self.mode

        if mode.user.write and account == self.owner:
            return True
        elif mode.group.write and account.customer == self.owner.customer:
            return True
        elif mode.other.write:
            return True
        else:
            return False

    def _executable_by(self, account):
        """Determines whether this inode is
        executable by a certain account
        """
        mode = self.mode

        if mode.user.execute and account == self.owner:
            return True
        elif mode.group.execute and account.customer == self.owner.customer:
            return True
        elif mode.other.execute:
            return True
        else:
            return False

    def _parents_readable(self, account):
        """Determines whether the parents of the INode are readable"""
        parent = self.inode.parent

        while parent is not None:
            if parent.isdir:
                if not parent._executable_by(account):
                    return False
            else:
                raise ConsistencyError(parent)

        return True

    def readable_by(self, account):
        """Determines whether the account can read this Inode"""
        return self._readable_by(account) and self._parents_readable(account)

    def writable_by(self, account):
        """Determines whether the account can write this Inode"""
        return self._writable_by(account) and self._parents_readable(account)

    def executable_by(self, account):
        """Determines whether the account can execute this Inode"""
        return self._executable_by(account) and self._parents_readable(account)
