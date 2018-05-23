"""ORM models."""

from logging import getLogger

from peewee import PrimaryKeyField, ForeignKeyField, IntegerField, CharField, \
    BigIntegerField

from filedb import FileError, add, delete, get, mimetype, sha256sum, size
from homeinfo.crm import Customer
from peeweeplus import MySQLDatabase, JSONModel

from hisfs.config import CONFIG
from hisfs.messages import ReadError, QuotaExceeded

__all__ = ['FileExists', 'File', 'Quota']


DATABASE = MySQLDatabase.from_config(CONFIG['db'])
PATHSEP = '/'


LOGGER = getLogger(__file__)


class FileExists(Exception):
    """Indicates that a file with the respective name already exists."""

    def __init__(self, file):
        """Sets the existing file."""
        super().__init__()
        self.file = file


class FSModel(JSONModel):
    """Basic immobit model."""

    class Meta:
        """Configures database and schema."""
        database = DATABASE
        schema = DATABASE.database

    id = PrimaryKeyField()


class File(FSModel):
    """Inode database model for the virtual filesystem."""

    name = CharField(255, db_column='name')
    customer = ForeignKeyField(Customer, db_column='customer')
    _file = IntegerField(column_name='file')

    @classmethod
    def add(cls, name, customer, bytes_):
        """Adds the respective file."""
        try:
            file = File.get((File.name == name) & (File.customer == customer))
        except cls.DoesNotExist:
            file = cls()
            file.name = name
            file.customer = customer
            file.bytes = bytes_
            file.save()
            return file

        raise FileExists(file)

    @property
    def bytes(self):
        """Returns the respective bytes."""
        try:
            return get(self._file)
        except FileError:
            raise ReadError()

    @bytes.setter
    def bytes(self, bytes_):
        """Sets the respective bytes."""
        try:
            delete(self._file)
        except FileError as file_error:
            LOGGER.error(file_error)

        self._file = add(bytes_)

    @property
    def sha256sum(self):
        """Returns the expected SHA-256 checksum."""
        try:
            return sha256sum(self._file)
        except FileError:
            raise ReadError()

    @property
    def mimetype(self):
        """Returns the MIME type."""
        try:
            return mimetype(self._file)
        except FileError:
            raise ReadError()

    @property
    def size(self):
        """Returns the size in bytes."""
        try:
            return size(self._file)
        except FileError:
            raise ReadError()

    def delete_instance(self, recursive=False, delete_nullable=False):
        """Removes the file."""
        try:
            delete(self._file)
        except FileError as file_error:
            LOGGER.error(file_error)

        return super().delete_instance(
            recursive=recursive, delete_nullable=delete_nullable)

    def to_dict(self):
        """Returns a JSON-ish dictionary."""
        dictionary = super().to_dict()
        dictionary.update({
            'sha256sum': self.sha256sum,
            'mimetype': self.mimetype,
            'size': self.size})
        return dictionary


class Quota(FSModel):
    """Quota settings for a customer."""

    customer = ForeignKeyField(Customer, db_column='customer')
    quota = BigIntegerField()   # Quota in bytes.

    @classmethod
    def by_customer(cls, customer):
        """Returns the settings for the respective customer."""
        return cls.get(cls.customer == customer)

    @property
    def files(self):
        """Yields media file records of the respective customer."""
        return File.select().where(File.customer == self.customer)

    @property
    def used(self):
        """Returns used space."""
        return sum(file.size for file in self.files)

    @property
    def free(self):
        """Returns free space for the respective customer."""
        return self.quota - self.used

    def alloc(self, bytec):
        """Tries to allocate the requested size in bytes."""
        if self.free < bytec:
            raise QuotaExceeded(quota=self.quota, free=self.free, bytec=bytec)

        return True

    def to_dict(self, **kwargs):
        """Returns a JSON compliant dictionary."""
        dictionary = super().to_dict(**kwargs)
        dictionary.update({
            'quota': self.quota,
            'free': self.free,
            'used': self.used})
        return dictionary
