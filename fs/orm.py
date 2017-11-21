"""ORM models."""

from contextlib import suppress

from peewee import DoesNotExist, Model, PrimaryKeyField, ForeignKeyField, \
    IntegerField, SmallIntegerField, CharField

from homeinfo.crm import Customer
from vfslib import PosixMode
from filedb import FileError, add, get, delete, sha256sum, mimetype, size

from his.orm import his_db, Account
from .messages import NotADirectory, NotAFile, ReadError, WriteError, \
    DirectoryNotEmpty

__all__ = ['Inode']


DATABASE = his_db('fs')
PATHSEP = '/'


class FSModel(Model):
    """Basic immobit model."""

    id = PrimaryKeyField()

    class Meta:
        database = DATABASE
        schema = DATABASE.database


class Inode(FSModel):
    """Inode database model for the virtual filesystem."""

    parent = ForeignKeyField('self', db_column='parent', null=True)
    name_ = CharField(255, db_column='name')
    owner = ForeignKeyField(Account, db_column='owner')
    group = ForeignKeyField(Customer, db_column='group')
    mode_ = SmallIntegerField(db_column='mode')
    file = IntegerField(null=True, default=None)

    @classmethod
    def by_owner(cls, owner=None, group=None):
        """Yields inodes that are owned by
        the respective owner and group.
        """
        if owner is None and group is None:
            raise ValueError('Must specify owner and/or group.')
        elif owner is not None and group is None:
            return cls.select().where(cls.owner == owner)
        elif owner is None and group is not None:
            return cls.select().where(cls.group == group)

        return cls.select().where((cls.owner == owner) & (cls.group == group))

    @classmethod
    def root_for(cls, owner=None, group=None):
        """Yields elements of the respective root folder."""
        if owner is None and group is None:
            return cls.select().where(cls.parent >> None)
        elif owner is not None and group is None:
            return cls.select().where(
                (cls.parent >> None) & (cls.owner == owner))
        elif owner is None and group is not None:
            return cls.select().where(
                (cls.parent >> None) & (cls.group == group))

        return cls.select().where(
            (cls.parent >> None) & (cls.owner == owner) & (cls.group == group))

    @classmethod
    def by_sha256sum(cls, sha256sum, owner=None, group=None):
        """Returns INodes by SHA-256 checksum match."""
        for inode in cls.by_owner(owner=owner, group=group):
            if inode.sha256sum == sha256sum:
                yield inode

    @classmethod
    def by_path_nodes(cls, nodes, owner=None, group=None):
        """Returns the respective Inode by the given node list."""
        if owner is None and group is None:
            raise ValueError('Must specify owner and/or group.')

        parent = None

        for node in nodes:
            if parent is None:
                if owner is None and group is not None:
                    parent = cls.get(
                        (cls.group == group) & (cls.parent >> None)
                        & (cls.name == node))
                elif owner is not None and group is None:
                    parent = cls.get(
                        (cls.owner == owner) & (cls.parent >> None)
                        & (cls.name == node))
                else:
                    parent = cls.get(
                        (cls.group == group) & (cls.owner == owner)
                        & (cls.parent >> None) & (cls.name == node))
            else:
                if owner is None and group is not None:
                    parent = cls.get(
                        (cls.group == group) & (cls.parent == parent)
                        & (cls.name == node))
                elif owner is not None and group is None:
                    parent = cls.get(
                        (cls.owner == owner) & (cls.parent == parent)
                        & (cls.name == node))
                else:
                    parent = cls.get(
                        (cls.group == group) & (cls.owner == owner)
                        & (cls.parent == parent) & (cls.name == node))

        return parent

    @classmethod
    def by_path(cls, path, owner=None, group=None):
        """Returns the Inode under the respective path."""
        root, *nodes = path.parts

        if root != PATHSEP:
            raise ValueError('Invalid root node: "{}".'.format(root))

        return cls.by_path_nodes(nodes, owner=owner, group=group)

    @property
    def name(self):
        """Returns the inode's name."""
        return self.name_

    @name.setter
    def name(self, name):
        """Sets the name"""
        if not name:
            raise ValueError('File name must not be empty.')
        elif PATHSEP in name:
            raise ValueError('File name must not contain "{}".'.format(
                PATHSEP))
        else:
            self.name_ = name

    @property
    def mode(self):
        """Returns the file mode."""
        return PosixMode.from_int(self.mode_)

    @mode.setter
    def mode(self, mode):
        """Sets the file mode."""
        self.mode_ = int(mode)

    @property
    def revpath(self):
        """Returns the reversed path nodes towards the inode."""
        yield self.name
        parent = self.parent

        while parent is not None:
            yield parent.name
            parent = parent.parent

        yield ''    # Root directory.

    @property
    def path(self):
        """Returns the path to the inode."""
        return PATHSEP.join(reversed(tuple(self.revpath)))

    @property
    def root(self):
        """Determines whether the inode is on the root level."""
        return self.parent is None

    @property
    def isdir(self):
        """Determines whether the inode is a directory."""
        return self.file is None

    @property
    def isfile(self):
        """Determines whether the inode is a file."""
        return not self.isdir

    @property
    def data(self):
        """Returns the file's content."""
        if self.file is None:
            raise NotAFile()

        try:
            return get(self.file)
        except FileError:
            raise ReadError()

    @data.setter
    def data(self, data):
        """Returns the file's content."""
        if self.file is None and self.id is not None:
            raise NotAFile()

        try:
            file_id = add(data)
        except FileError:
            raise WriteError()
        else:
            with suppress(FileError):
                delete(self.file)

            self.file = file_id

    @property
    def sha256sum(self):
        """Returns the expected SHA-256 checksum."""
        if self.file is None:
            raise NotAFile()

        try:
            return sha256sum(self.file)
        except FileError:
            raise ReadError() from None

    @property
    def mimetype(self):
        """Returns the MIME type."""
        if self.file is None:
            raise NotAFile()

        try:
            return mimetype(self.file)
        except FileError:
            raise ReadError() from None

    @property
    def size(self):
        """Returns the size in bytes."""
        if self.file is None:
            raise NotAFile()

        try:
            return size(self.file)
        except FileError:
            raise ReadError() from None

    @property
    def children(self):
        """Yields the directoie's children."""
        if self.isdir:
            return self.__class__.select().where(self.__class__.parent == self)

        raise NotADirectory()

    def remove(self, recursive=False):
        """Removes a virtual inode."""
        if recursive:
            for child in self.__class__.select().where(
                    self.__class__.parent == self):
                child.remove(recursive=True)

        self.unlink()

    def unlink(self):
        """Deletes a virtual inode."""
        try:
            self.__class__.get(self.__class__.parent == self)
        except DoesNotExist:
            if self.file is not None:
                delete(self.file)

            self.delete_instance()

        raise DirectoryNotEmpty()

    def to_dict(self, children=True, mimetype=True, size=True):
        """Converts the inode into a dictionary."""
        dictionary = {
            'name': self.name,
            'owner': repr(self.owner),
            'group': repr(self.group),
            'mode': str(self.mode),
            'directory': self.isdir}

        if self.isdir:
            if children:
                dictionary['children'] = list(self.lsdir_dict(validate=False))
        else:
            if mimetype:
                dictionary['mimetype'] = self.mimetype

            if size:
                dictionary['size'] = self.size

        return dictionary

    def lsdir_dict(self, validate=True):
        """List directory contents."""
        if validate and not self.isdir:
            raise NotADirectory()

        for child in self.children:
            yield child.to_dict(children=False, mimetype=False, size=False)

    def dict_for(self, account):
        """Converts the inode into a dictionary
        considering access permissions.
        """
        if (self.parent or self).executable_by(account):
            dictionary = self.to_dict(children=False)

            if self.isdir:
                dictionary['children'] = [
                    child.to_dict(account) for child in self.children]

            return dictionary

        return {}

    def _readable_by(self, account):
        """Determines whether this inode is
        readable by a certain account.
        """
        return any((
            account.root,
            self.mode.user.read and account == self.owner,
            self.mode.group.read and account.customer == self.owner.customer,
            self.mode.other.read))

    def _writable_by(self, account):
        """Determines whether this inode is
        writable by a certain account.
        """
        return any((
            self.mode.user.write and account == self.owner,
            self.mode.group.write and account.customer == self.owner.customer,
            self.mode.other.write))

    def _executable_by(self, account):
        """Determines whether this inode is
        executable by a certain account.
        """
        return any((
            self.mode.user.execute and account == self.owner,
            self.mode.group.execute and account.customer == self.owner.customer,
            self.mode.other.execute))

    def _parents_readable(self, account):
        """Determines whether the parents of the Inode are readable."""
        if self.parent is not None:
            return self.parent.executable_by(account)

        return True

    def readable_by(self, account):
        """Determines whether the account can read this Inode."""
        return self._readable_by(account) and self._parents_readable(account)

    def writable_by(self, account):
        """Determines whether the account can write this Inode."""
        return self._writable_by(account) and self._parents_readable(account)

    def executable_by(self, account):
        """Determines whether the account can execute this Inode."""
        return self._executable_by(account) and self._parents_readable(account)
