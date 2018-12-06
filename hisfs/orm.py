"""ORM models."""

from contextlib import suppress
from logging import getLogger

from peewee import ForeignKeyField, IntegerField, CharField, BigIntegerField

from filedb import FileError, add, delete, get, mimetype, sha256sum, size
from mdb import Customer
from peeweeplus import MySQLDatabase, JSONModel

from hisfs.config import CONFIG
from hisfs.exceptions import UnsupportedFileType, NoThumbnailRequired
from hisfs.messages import ReadError, QuotaExceeded
from hisfs.thumbnails import gen_thumbnail


__all__ = ['FileExists', 'File', 'Quota']


DATABASE = MySQLDatabase.from_config(CONFIG['db'])
PATHSEP = '/'
LOGGER = getLogger(__file__)
IMAGE_MIMETYPES = {'image/jpeg', 'image/png'}


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


class FileMixin:
    """Common file mixin."""

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

    def to_json(self):
        """Returns a JSON-ish dictionary."""
        json = super().to_json()
        json.update({
            'sha256sum': self.sha256sum,
            'mimetype': self.mimetype,
            'size': self.size})
        return json


class BasicFile(FSModel, FileMixin):
    """Common files model."""

    def delete_instance(self, recursive=False, delete_nullable=False):
        """Removes the file."""
        try:
            delete(self._file)
        except FileError as file_error:
            LOGGER.error(file_error)

        return super().delete_instance(
            recursive=recursive, delete_nullable=delete_nullable)


class File(BasicFile):
    """Inode database model for the virtual filesystem."""

    name = CharField(255, column_name='name')
    customer = ForeignKeyField(Customer, column_name='customer')
    _file = IntegerField(column_name='file')

    @classmethod
    def add(cls, name, customer, bytes_, rename=False, *, suffix=0):
        """Adds the respective file."""
        if rename and suffix:
            name += ' ({})'.format(suffix)

        try:
            file = File.get((File.name == name) & (File.customer == customer))
        except cls.DoesNotExist:
            file = cls()
            file.name = name
            file.customer = customer
            file.bytes = bytes_
            file.save()
            return file

        if rename:
            return cls.add(
                name, customer, bytes_, rename=rename, suffix=suffix+1)

        raise FileExists(file)

    @property
    def is_image(self):
        """Determines whether this file is an image."""
        return self.mimetype in IMAGE_MIMETYPES

    def thumbnail(self, resolution):
        """Returns a thumbnail with the respective resolution."""
        if self.is_image:
            return Thumbnail.from_file(self, resolution)

        raise UnsupportedFileType()

    def delete_instance(self, recursive=False, delete_nullable=False):
        """Removes the file."""
        for thumbnail in self.thumbnails:
            thumbnail.delete_instance()

        return super().delete_instance(
            recursive=recursive, delete_nullable=delete_nullable)


class Thumbnail(BasicFile):
    """An image thumbnail."""

    file = ForeignKeyField(File, column_name='file', backref='thumbnails')
    size_x = IntegerField()
    size_y = IntegerField()
    _file = IntegerField(column_name='filedb_file')

    @classmethod
    def from_file(cls, file, resolution):
        """Creates a thumbnail from the respective file."""
        size_x, size_y = resolution

        with suppress(cls.DoesNotExist):
            return cls.get(
                (cls.file == file)
                & (cls.size_x == size_x)
                & (cls.size_y == size_y))

        try:
            bytes_ = gen_thumbnail(file.bytes, resolution)
        except NoThumbnailRequired:
            return file

        thumbnail = cls()
        thumbnail.file = file
        thumbnail.size_x = size_x
        thumbnail.size_y = size_y
        thumbnail.bytes = bytes_
        thumbnail.save()
        return thumbnail


class Quota(FSModel):
    """Quota settings for a customer."""

    customer = ForeignKeyField(Customer, column_name='customer')
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

    def to_json(self, **kwargs):
        """Returns a JSON-ish dictionary."""
        json = super().to_json(**kwargs)
        json.update({
            'quota': self.quota,
            'free': self.free,
            'used': self.used})
        return json
