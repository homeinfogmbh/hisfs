"""ORM models."""

from contextlib import suppress
from functools import lru_cache
from pathlib import Path

from peewee import ForeignKeyField, IntegerField, CharField, BigIntegerField

from filedb import META_FIELDS, File as FileDBFile
from mdb import Customer
from peeweeplus import MySQLDatabase, JSONModel

from hisfs.config import CONFIG
from hisfs.exceptions import FileExists
from hisfs.exceptions import UnsupportedFileType
from hisfs.exceptions import NoThumbnailRequired
from hisfs.exceptions import QuotaExceeded
from hisfs.thumbnails import gen_thumbnail


__all__ = ['File', 'Quota']


DATABASE = MySQLDatabase.from_config(CONFIG['db'])
PATHSEP = '/'
IMAGE_MIMETYPES = {'image/jpeg', 'image/png'}


@lru_cache(64)
def _get_sparse_file(ident):
    """Returns a sparse filedb.File without binary data."""

    return FileDBFile.select(*META_FIELDS).where(FileDBFile.id == ident).get()


class FSModel(JSONModel):
    """Basic immobit model."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE
        schema = DATABASE.database


class BasicFile(FSModel):
    """Common files model."""

    filedb_file = ForeignKeyField(FileDBFile, column_name='filedb_file')

    @property
    def metadata(self):
        """Returns the file meta data."""
        return _get_sparse_file(self.filedb_file_id)

    @property
    def bytes(self):
        """Returns the file's bytes."""
        return self.filedb_file.bytes

    def stream(self):
        """Returns HTTP stream."""
        return self.filedb_file.stream()

    def to_json(self, *args, **kwargs):
        """Returns a JSON-ish dictionary."""
        json = super().to_json(*args, **kwargs)
        metadata = {
            'sha256sum': self.metadata.sha256sum,
            'mimetype': self.metadata.mimetype,
            'size': self.metadata.size
        }
        json.update(metadata)
        return json

    def save(self, *args, **kwargs):
        """Saves the filedb.File first."""
        if self.filedb_file:
            self.filedb_file.save(*args, **kwargs)

        return super().save(*args, **kwargs)


class File(BasicFile):  # pylint: disable=R0901
    """Inode database model for the virtual filesystem."""

    name = CharField(255, column_name='name')
    customer = ForeignKeyField(Customer, column_name='customer')

    @classmethod
    def add(cls, name, customer, bytes_, *, rename=False, suffix=0):
        """Adds the respective file."""
        if rename and suffix:
            path = Path(name)
            name = path.stem + f' ({suffix})' + path.suffix

        try:
            file = cls.get((cls.name == name) & (cls.customer == customer))
        except cls.DoesNotExist:
            file = cls()
            file.name = name
            file.customer = customer
            file.filedb_file = FileDBFile.from_bytes(bytes_)
            return file

        if rename:
            return cls.add(
                name, customer, bytes_, rename=rename, suffix=suffix+1)

        raise FileExists(file)

    @property
    def is_image(self):
        """Determines whether this file is an image."""
        return self.metadata.mimetype in IMAGE_MIMETYPES

    def thumbnail(self, resolution):
        """Returns a thumbnail with the respective resolution."""
        if self.is_image:
            return Thumbnail.from_file(self, resolution)

        raise UnsupportedFileType()


class Thumbnail(BasicFile):     # pylint: disable=R0901
    """An image thumbnail."""

    file = ForeignKeyField(
        File, column_name='file', backref='thumbnails', on_delete='CASCADE')
    size_x = IntegerField()
    size_y = IntegerField()

    @classmethod
    def from_file(cls, file, resolution):
        """Creates a thumbnail from the respective file."""
        size_x, size_y = resolution

        with suppress(cls.DoesNotExist):
            return cls.get(
                (cls.file == file)
                & ((cls.size_x == size_x) | (cls.size_y == size_y)))

        filedb_file = file.filedb_file

        try:
            bytes_, resolution = gen_thumbnail(
                filedb_file.bytes, resolution, filedb_file.mimetype)
        except NoThumbnailRequired:
            return file

        thumbnail = cls()
        thumbnail.file = file
        thumbnail.size_x, thumbnail.size_y = resolution
        thumbnail.filedb_file = FileDBFile.from_bytes(bytes_, save=True)
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
        """Yields file records of the respective customer."""
        return File.select().where(File.customer == self.customer)

    @property
    def used(self):
        """Returns used space."""
        return sum(file.metadata.size for file in self.files.iterator())

    @property
    def free(self):
        """Returns free space for the respective customer."""
        return self.quota - self.used

    def alloc(self, bytec):
        """Tries to allocate the requested size in bytes."""
        free = self.free

        if free < bytec:
            raise QuotaExceeded(quota=self.quota, free=free, bytec=bytec)

        return True

    def to_json(self, **kwargs):
        """Returns a JSON-ish dictionary."""
        json = super().to_json(**kwargs)
        json.update({
            'quota': self.quota,
            'free': self.free,
            'used': self.used
        })
        return json
