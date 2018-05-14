"""ORM models."""

from logging import getLogger

from peewee import PrimaryKeyField, ForeignKeyField, IntegerField, CharField, \
    BigIntegerField

from filedb import FileError, add, delete, get, mimetype, sha256sum, size
from his.orm import Account
from homeinfo.crm import Customer
from peeweeplus import MySQLDatabase, JSONModel

from hisfs.config import CONFIG
from hisfs.messages import FileExists, ReadError, QuotaExceeded

__all__ = ['File']


DATABASE = MySQLDatabase(
    CONFIG['db']['db'], host=CONFIG['db']['host'], user=CONFIG['db']['user'],
    passwd=CONFIG['db']['passwd'], closing=True)
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


LOGGER = getLogger(__file__)


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
    account = ForeignKeyField(Account, db_column='account')
    _file = IntegerField(column_name='file')

    @classmethod
    def add(cls, name, account, data):
        """Adds the respective file."""
        try:
            File.get((File.name == name) & (File.account == account))
        except cls.DoesNotExist:
            file = cls()
            file.name = name
            file.account = account
            file.data = data
            file.save()
            return file

        raise FileExists(name=name)

    @property
    def data(self):
        """Returns the respective data."""
        try:
            return get(self._file)
        except FileError:
            raise ReadError()

    @data.setter
    def data(self, data):
        """Sets the respective data."""
        try:
            delete(self._file)
        except FileError as file_error:
            LOGGER.error(file_error)

        self._file = add(data)

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


class CustomerQuota(FSModel):
    """Media settings for a customer."""

    class Meta:
        """Set table name."""
        table_name = 'customer_quota'

    customer = ForeignKeyField(Customer, db_column='customer')
    quota = BigIntegerField(default=DEFAULT_QUOTA)     # Quota in bytes.

    @classmethod
    def by_customer(cls, customer):
        """Returns the settings for the respective customer."""
        return cls.get(cls.customer == customer)

    @property
    def files(self):
        """Yields media file records of the respective customer."""
        return File.select().join(Account).where(
            (Account.customer == self.customer))

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
