"""ORM models."""

from contextlib import suppress

from peewee import Model, PrimaryKeyField, ForeignKeyField, \
    IntegerField, SmallIntegerField, CharField

from homeinfo.crm import Customer
from vfslib import PosixMode
from filedb import FileError, add, get, delete, sha256sum, mimetype, size

from his.orm import his_db, Account
from .messages import NotADirectory, NotAFile, ReadError, WriteError, \
    DirectoryNotEmpty, QuotaExceeded

__all__ = ['Inode']


DATABASE = his_db('fs')
PATHSEP = '/'
BINARY_FACTOR = 1024
DECIMAL_FACTOR = 1000
BYTE = 1
KILOBYTE = DECIMAL_FACTOR * BYTE
KIBIBYTE = BINARY_FACTOR * BYTE
MEGABYTE = DECIMAL_FACTOR * KILOBYTE
MEBIBYTE = BINARY_FACTOR * KIBIBYTE
GIGABYTE = DECIMAL_FACTOR * MEGABYTE
GIBIBATE = BINARY_FACTOR * MEBIBYTE
DEFAULT_QUOTA = 5 * GIBIBATE    # 5.0 GiB.


def ownerselect(owner=None, group=None):
    """Returns an expression for the respective owner and group."""

    expression = True

    if owner is not None:
        expression &= cls.owner == owner

    if group is not None:
        expression &= cls.group == group

    return expression


class FSModel(Model):
    """Basic immobit model."""

    id = PrimaryKeyField()

    class Meta:
        database = DATABASE
        schema = DATABASE.database


class Inode(FSModel):
    """Inode database model for the virtual filesystem."""

    parent = ForeignKeyField(
        'self', db_column='parent', null=True, on_delete='CASCADE')
    name_ = CharField(255, db_column='name')
    owner = ForeignKeyField(Account, db_column='owner')
    group = ForeignKeyField(Customer, db_column='group')
    mode_ = SmallIntegerField(db_column='mode')
    _file = IntegerField(null=True)

    @classmethod
    def owner_context(cls, owner, group):
        """Sets owner and group."""
        return OwnerContext(cls, owner, group)

    @classmethod
    def by_owner(cls, owner=None, group=None):
        """Yields inodes that are owned by
        the respective owner and group.
        """
        return cls.select().where(ownerselect(owner=owner, group=group))

    @classmethod
    def root_for(cls, owner=None, group=None):
        """Yields elements of the respective root folder."""
        return cls.select().where((cls.parent >> None) & ownerselect(
            owner=owner, group=group))

    @classmethod
    def by_sha256sum(cls, sha256sum, owner=None, group=None):
        """Returns INodes by SHA-256 checksum match."""
        for inode in cls.by_owner(owner=owner, group=group):
            if inode.sha256sum == sha256sum:
                yield inode

    @classmethod
    def by_id(cls, ident, owner=None, group=None):
        """Returns the respective Inode by the given ID."""
        return cls.get((cls.id == ident) & ownerselect(
            owner=owner, group=group))

    @classmethod
    def by_path_nodes(cls, nodes, owner=None, group=None):
        """Returns the respective Inode by the given node list."""
        if owner is None and group is None:
            raise ValueError('Must specify owner and/or group.')

        parent = None

        for node in nodes:
            expression = cls.name == node

            if parent is None:
                expression &= cls.parent >> None
            else:
                expression &= cls.parent == parent

            if owner is not None:
                expression &= cls.owner == owner

            if group is not None:
                expression &= cls.group == group

            try:
                parent = cls.get(expression)
            except cls.DoesNotExist:
                raise FileNotFoundError()

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
    def parents(self):
        """Yields the inode's parents."""
        if self.parent is not None:
            yield self.parent
            yield from self.parent.parents

    @property
    def revpath(self):
        """Returns the reversed path nodes towards the inode."""
        yield self.name

        for parent in self.parents:
            yield parent.name

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
        return self._file is None

    @property
    def isfile(self):
        """Determines whether the inode is a file."""
        return not self.isdir

    @property
    def type(self):
        """Returns the Inode's type."""
        return 'directory' if self.isdir else 'file'

    @property
    def data(self):
        """Returns the file's content."""
        if self._file is None:
            raise NotAFile()

        try:
            return get(self._file)
        except FileError:
            raise ReadError()

    @data.setter
    def data(self, data):
        """Returns the file's content."""
        if self._file is None and self.id is not None:
            raise NotAFile()

        try:
            file_id = add(data)
        except FileError:
            raise WriteError()
        else:
            with suppress(FileError):
                delete(self._file)

            self._file = file_id

    @property
    def sha256sum(self):
        """Returns the expected SHA-256 checksum."""
        if self._file is None:
            raise NotAFile()

        try:
            return sha256sum(self._file)
        except FileError:
            raise ReadError() from None

    @property
    def mimetype(self):
        """Returns the MIME type."""
        if self._file is None:
            raise NotAFile()

        try:
            return mimetype(self._file)
        except FileError:
            raise ReadError() from None

    @property
    def size(self):
        """Returns the size in bytes."""
        if self._file is None:
            raise NotAFile()

        try:
            return size(self._file)
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
        except self.__class__.DoesNotExist:
            if self._file is not None:
                delete(self._file)

            self.delete_instance()

        raise DirectoryNotEmpty()

    def to_dict(self, children=True):
        """Converts the inode into a dictionary."""
        dictionary = {
            'name': self.name,
            'owner': repr(self.owner),
            'group': repr(self.group),
            'mode': str(self.mode),
            'type': self.type}

        if self.isdir:
            if children:
                dictionary['content'] = [
                    child.to_dict(children=False) for child in self.children]
        else:
            dictionary['mimetype'] = self.mimetype
            dictionary['size'] = self.size

        return dictionary

    def readable_by(self, user, group):
        """Determines whether this inode is
        readable by a certain account.
        """
        return any((
            user.root,
            self.mode.user.read and self.owner == user,
            self.mode.group.read and self.group == group,
            self.mode.other.read))

    def writable_by(self, user, group):
        """Determines whether this inode is
        writable by a certain account.
        """
        return any((
            user.root,
            self.mode.user.write and self.owner == user,
            self.mode.group.write and self.group == group,
            self.mode.other.write))

    def executable_by(self, user, group):
        """Determines whether this inode is
        executable by a certain account.
        """
        return any((
            user.root,
            self.mode.user.execute and self.owner == user,
            self.mode.group.execute and self.group == group,
            self.mode.other.execute))


class CustomerQuota(FSModel):
    """Media settings for a customer."""

    customer = ForeignKeyField(Customer, db_column='customer')
    quota = IntegerField(default=DEFAULT_QUOTA)     # Quota in bytes.

    @classmethod
    def by_customer(cls, customer):
        """Returns the settings for the respective customer."""
        return cls.get(cls.customer == customer)

    @property
    def files(self):
        """Yields media file records of the respective customer."""
        return Inode.select().where(
                (Inode.group == self.customer) & ~(Inode.file >> None))

    @property
    def used(self):
        """Returns used space."""
        return sum(file.size for file in self.files)

    @property
    def free(self):
        """Returns free space for the respective customer."""
        return self.quota - self.used

    def alloc(self, size):
        """Tries to allocate the requested size in bytes."""
        if self.free < size:
            raise QuotaExceeded(quota=self.quota)

        return True

    def to_dict(self, **kwargs):
        """Returns a JSON compliant dictionary."""
        dictionary = super().to_dict(**kwargs)
        dictionary.update({
            'quota': self.quota,
            'free': self.free,
            'used': self.used})
        return dictionary
