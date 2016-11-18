"""ORM models"""

from contextlib import suppress

from peewee import DoesNotExist, ForeignKeyField, IntegerField, CharField

from homeinfo.lib.fs import FileMode
from filedb import FileError, FileClient

from his.orm import module_model, Account
from his.fs.errors import NotADirectory, NotAFile, NoSuchNode, ReadError, \
    WriteError, DirectoryNotEmpty

__all__ = ['Inode']


class Inode(module_model('fs')):
    """Inode database model for the virtual filesystem"""

    PATHSEP = '/'
    FILE_CLIENT = FileClient('7958faef-01c9-4c3b-b4ef-1aecea6945c1')

    _name = CharField(255, db_column='name')
    owner = ForeignKeyField(Account, db_column='owner')
    parent = ForeignKeyField(
        'self', db_column='parent',
        null=True, default=None)
    file = IntegerField(null=True, default=None)
    _mode = IntegerField(db_column='mode')  # SMALLINT field!

    @classmethod
    def for_account(cls, account):
        """Returns fs nodes visible to the account"""
        # TODO: implement
        pass

    @classmethod
    def by_owner(cls, owner=None, group=None):
        """Yields elements of the respective root folder"""
        if owner is None and group is None:
            yield from cls
        elif owner is not None:
            for inode in cls.select().where(cls.owner == owner):
                if group is not None:
                    if inode.owner.customer == group:
                        yield inode
                else:
                    yield inode
        else:
            for inode in cls:
                if inode.owner.customer == group:
                    yield inode

    @classmethod
    def getrel(cls, name, parent, owner):
        """Get inode by relative properties.

        XXX: Only <parent> may be None for root nodes.
        """
        if parent is None:
            return cls.get(
                (cls._name == name) &
                (cls.parent >> None) &
                (cls.owner == owner))
        else:
            return cls.get(
                (cls._name == name) &
                (cls.parent == parent) &
                (cls.owner == owner))

    @classmethod
    def root(cls, owner=None, group=None):
        """Yields elements of the respective root folder"""
        for record in cls.by_owner(owner=owner, group=group):
            if record.parent is None:
                yield record

    @classmethod
    def by_revpath(cls, revpath, owner=None, group=None):
        """Finds records by reversed path nodes"""
        walked = ['']
        parent = None

        while revpath:
            node = revpath.pop()
            walked.append(node)

            try:
                parent = cls.getrel(node, parent, owner=owner, group=group)
            except DoesNotExist:
                raise NoSuchNode(cls.PATHSEP.join(walked))
            else:
                # Bail out if the node is a file
                # but is expected to have children.
                if parent.isfile and revpath:
                    raise NotADirectory(cls.PATHSEP.join(walked))

        return parent

    @classmethod
    def by_path(cls, path, owner=None, group=None):
        """Yields files and directories by the respective path"""
        return cls.by_revpath(
            list(reversed(path.split(cls.PATHSEP))),
            owner=owner, group=group)

    @classmethod
    def fsdict(cls, owner=None, group=None):
        """Converts the file system to a dictionary"""
        return {'children': [child.to_dict() for child in cls.by_owner(
            owner=owner, group=group)]}

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
        if self.file is None:
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
                self.FILE_CLIENT.sha256sum(self.file)
            except FileError:
                raise ReadError() from None

    @property
    def children(self):
        """Yields the directoie's children"""
        if self.isdir:
            return self.__class__.select().where(self.__class__.parent == self)
        else:
            raise NotADirectory()

    @property
    def mode(self):
        """Returns the file mode"""
        return FileMode(self._mode)

    @mode.setter
    def mode(self, mode):
        """Sets the file mode"""
        self._mode = int(mode)

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
            with suppress(FileError):
                self.FILE_CLIENT.delete(self.file)

        self.delete_instance()

    def to_dict(self, recursive=False, hash=False):
        """Converts the inode into a dictionary"""
        result = {'name': self.name}

        if self.isdir:
            if recursive:
                result['children'] = [
                    child.to_dict(recursive=True, hash=hash) for
                    child in self.children]
            elif recursive is not None:
                # If recursive is false but not None, add only the  children
                # of the directory withour further recursion (default).
                result['children'] = [
                    child.to_dict(recursive=None, hash=hash) for
                    child in self.children]
        elif hash:
            try:
                result['sha256sum'] = self.FILE_CLIENT.sha256sum(self.file)
            except FileError:
                result['tainted'] = True

        return result

    def readable_by(self, account):
        """Determines whether this inode is
        readable by a certain account
        """
        if account == self.owner:
            if self.mode.user.read:
                return True

        if account.customer == self.owner.customer:
            if self.mode.group.read:
                return True

        if self.mode.other.read:
            return True

        return False

    def writable_by(self, account):
        """Determines whether this inode is
        writable by a certain account
        """
        if account == self.owner:
            if self.mode.user.write:
                return True

        if account.customer == self.owner.customer:
            if self.mode.group.write:
                return True

        if self.mode.other.write:
            return True

        return False

    def executable_by(self, account):
        """Determines whether this inode is
        executable by a certain account
        """
        if account == self.owner:
            if self.mode.user.execute:
                return True

        if account.customer == self.owner.customer:
            if self.mode.group.execute:
                return True

        if self.mode.other.execute:
            return True

        return False

    def accessible_by(self, account):
        """Determines whether this inode is
        accessible by a certain account
        """
        return self.readable_by(account) and (
            self.isfile or self.executable_by(account))
