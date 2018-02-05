"""ORM models."""

from peewee import MySQLDatabase, Model, PrimaryKeyField, ForeignKeyField, \
    IntegerField, CharField

from his.orm import Account
from homeinfo.crm import Customer
from filedb import FileError, sha256sum, mimetype, size, FileProperty

from hisfs.config import CONFIG
from hisfs.messages import ReadError, QuotaExceeded

__all__ = ['File']


DATABASE = MySQLDatabase(
    CONFIG['db']['database'], host=CONFIG['db']['host'],
    user=CONFIG['db']['user'], passwd=CONFIG['db']['passwd'], closing=True)
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


class FSModel(Model):
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
    _file = IntegerField(null=True)
    data = FileProperty(_file)

    @classmethod
    def add(cls, name, account, data):
        """Adds the respective file."""
        file = cls()
        file.name = name
        file.account = account
        file.data = data
        file.save()
        return file

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
