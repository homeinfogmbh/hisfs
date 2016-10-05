"""ORM models"""

from peewee import Model, PrimaryKeyField, ForeignKeyField, IntegerField, \
    CharField

from homeinfo.crm import Customer
from homeinfo.peewee import MySQLDatabase

from filedb import FileClient

from his.orm import Account

from .errors import NotADirectory, NotAFile, NoSuchNode, ReadError, \
    WriteError, DirectoryNotEmpty

__all__ = [
    'FileSystemError',
    'NotADirectory',
    'NotAFile',
    'NoSuchNode',
    'ReadError',
    'WriteError',
    'DirectoryNotEmpty',
    'Inode']


class FileSystemError(Exception):
    """Indicates errors within the file system"""

    pass


class NotADirectory(FileSystemError):
    """Indicates that an inode is not a
    directory but was expected to be one
    """

    def __init__(self, path):
        super().__init__(path)
        self.path = path


class NotAFile(FileSystemError):
    """Indicates that an inode is not a
    file but was expected to be one
    """

    pass


class NoSuchNode(FileSystemError):
    """Indicates that the respective path node does not exists"""

    def __init__(self, path):
        super().__init__(path)
        self.path = path


class ReadError(FileSystemError):
    """Indicates that no data could be read from filedb"""

    pass


class WriteError(FileSystemError):
    """Indicates that no data could be written to filedb"""

    pass


class DirectoryNotEmpty(FileSystemError):
    """Indicates that the directory could
    not be deleted because it is not empty
    """

    pass


class HISFSModel(Model):
    """Common HIS fs model"""

    class Meta:
        database = MySQLDatabase(
            'his_fs',
            host='localhost',
            user='crm',
            passwd='Z"XO;$2K+>XEo}jK>6-+}|U@,|E/6_&W',
            closing=True)
        schema = database.database

    id = PrimaryKeyField()


class Inode(HISFSModel):
    """Inode database model for the virtual filesystem"""

    PATHSEP = '/'

    _name = CharField(255, db_column='name')
    owner = ForeignKeyField(Account, db_column='owner')
    group = ForeignKeyField(Customer, db_column='group')
    parent = ForeignKeyField(
        'self', db_column='parent', null=True, default=None)
    file = IntegerField(null=True, default=None)

    @classmethod
    def by_owner(cls, owner=None, group=None):
        """Yields elements of the respective root folder"""
        if owner is None and group is None:
            return cls
        elif owner is not None and group is not None:
            return cls.select().where(
                (cls.owner == owner) &
                (cls.group == group))
        elif owner is not None:
            return cls.select().where((cls.owner == owner))
        elif group is not None:
            return cls.select().where((cls.group == group))
        else:
            raise ValueError()

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

            if parent is None:
                for record in cls.by_owner(owner=owner, group=group):
                    if record.parent is None and record.name == node:
                        if record.isdir or not revpath:
                            parent = record
                            break
                        else:
                            raise NotADirectory(cls.PATHSEP.join(walked))
                else:
                    raise NoSuchNode(cls.PATHSEP.join(walked))
            else:
                for record in cls.by_owner(owner=owner, group=group):
                    if record.parent == parent and record.name == node:
                        if record.isdir or not revpath:
                            parent = record
                            break
                        else:
                            raise NotADirectory(cls.PATHSEP.join(walked))
                else:
                    raise NoSuchNode(cls.PATHSEP.join(walked))

        return parent

    @classmethod
    def by_path(cls, path, owner=None, group=None):
        """Yields files and directories by the respective path"""
        return cls.by_revpath(
            list(reversed(path.split(cls.PATHSEP))),
            owner=None, group=None)

    @classmethod
    def fsdict(cls, owner=None, grup=None):
        """Converts the file system to a dictionary"""
        return {'children': [child.todict() for child in cls.by_owner(
            owner=owner, group=grup)]}

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
    def client(self):
        """Returns the filedb client"""
        return FileClient('7958faef-01c9-4c3b-b4ef-1aecea6945c1')

    @property
    def data(self):
        """Returns the file's content"""
        if self.file is None:
            raise NotAFile()
        else:
            try:
                return file_client.get(self.file)
            except FileError:
                raise ReadError()

    @data.setter
    def data(self, data):
        """Returns the file's content"""
        if self.file is None:
            raise NotAFile()
        else:
            try:
                file_id = self.client.add(data)
            except FileError:
                raise WriteError()
            else:
                with suppress(FileError):
                    self.client.delete(self.file)

                self.file = file_id

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
            first_child = self.__class__.get(self.__class__.parent == self)
        except DoesNotExist:
            pass
        else:
            raise DirectoryNotEmpty()

        if self.file is not None:
            with suppress(FileError):
                self.client.delete(self.file)

        self.delete_instance()

    def todict(self):
        """Converts the inode into a dictionary"""
        result = {'name': self.name}

        if self.isfile:
            with suppress(FileError):
                result['sha256sum'] = self.client.sha256sum(self.file)
        else:
            result['children'] = [child.todict() for child in self.children]

        return result
