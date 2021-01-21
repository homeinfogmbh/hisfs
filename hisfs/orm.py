"""ORM models."""

from __future__ import annotations
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Tuple, Union

from flask import Response
from peewee import BigIntegerField
from peewee import CharField
from peewee import ForeignKeyField
from peewee import IntegerField
from peewee import ModelSelect

from filedb import File as FileDBFile
from mdb import Customer
from peeweeplus import MySQLDatabase, JSONModel

from hisfs.config import CONFIG
from hisfs.exceptions import FileExists
from hisfs.exceptions import UnsupportedFileType
from hisfs.exceptions import NoThumbnailRequired
from hisfs.exceptions import QuotaExceeded
from hisfs.thumbnails import gen_thumbnail


__all__ = ['File', 'Thumbnail', 'Quota']


DATABASE = MySQLDatabase.from_config(CONFIG['db'])
PATHSEP = '/'
IMAGE_MIMETYPES = {'image/jpeg', 'image/png'}


class FSModel(JSONModel):
    """Basic immobit model."""

    class Meta:     # pylint: disable=C0111,R0903
        database = DATABASE
        schema = DATABASE.database


class BasicFile(FSModel):
    """Common files model."""

    filedb_file = ForeignKeyField(
        FileDBFile, column_name='filedb_file', lazy_load=False)

    @classmethod
    def select(cls, *args, cascade: bool = False, **kwargs):
        """Makes a select with or without bytes."""
        if cascade:
            return super().select(cls, FileDBFile).join(FileDBFile)

        return super().select(*args, **kwargs)

    @property
    def bytes(self) -> bytes:
        """Returns the bytes."""
        return self.filedb_file.bytes

    @property
    def mimetype(self) -> str:
        """Returns the MIME type."""
        return self.filedb_file.mimetype

    @property
    def sha256sum(self) -> str:
        """Returns the SHA-256 checksum."""
        return self.filedb_file.sha256sum

    @property
    def size(self) -> int:
        """Returns the file size."""
        return self.filedb_file.size

    @property
    def created(self) -> datetime:
        """Returns the create datetime."""
        return self.filedb_file.created

    @property
    def last_access(self) -> datetime:
        """Returns the last access datetime."""
        return self.filedb_file.last_access

    @property
    def accessed(self) -> int:
        """Returns the access count."""
        return self.filedb_file.accessed

    @property
    def is_image(self) -> bool:
        """Determines whether this file is an image."""
        return self.mimetype in IMAGE_MIMETYPES

    def stream(self) -> Response:
        """Returns HTTP stream."""
        return self.filedb_file.stream()

    def to_json(self, **_) -> dict:
        """Returns a JSON-ish dictionary."""
        return {
            'id': self.id,
            'mimetype': self.mimetype,
            'sha256sum': self.sha256sum,
            'size': self.size,
            'created': self.created,
            'lastAccess': self.last_access,
            'accessed': self.accessed
        }

    def save(self, *args, **kwargs) -> int:
        """Saves the filedb.File first."""
        if self.filedb_file:
            self.filedb_file.save(*args, **kwargs)

        return super().save(*args, **kwargs)


class File(BasicFile):  # pylint: disable=R0901
    """Inode database model for the virtual filesystem."""

    name = CharField(255, column_name='name')
    customer = ForeignKeyField(
        Customer, column_name='customer', lazy_load=False)

    @classmethod
    def add(cls, name: str, customer: Union[Customer, int], bytes_: bytes, *,
            rename: bool = False, suffix: int = 0) -> File:
        """Adds the respective file."""
        if rename and suffix:
            path = Path(name)
            name = f'{path.stem} ({suffix}){path.suffix}'

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

    def thumbnail(self, resolution: Tuple[int, int]) -> Thumbnail:
        """Returns a thumbnail with the respective resolution."""
        if self.is_image:
            return Thumbnail.from_file(self, resolution)

        raise UnsupportedFileType()


class Thumbnail(BasicFile):     # pylint: disable=R0901
    """An image thumbnail."""

    file = ForeignKeyField(
        File, column_name='file', backref='thumbnails', on_delete='CASCADE',
        on_update='CASCADE', lazy_load=False)
    size_x = IntegerField()
    size_y = IntegerField()

    @classmethod
    def from_file(cls, file: File, resolution: Tuple[int, int]) -> Thumbnail:
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

    customer = ForeignKeyField(
        Customer, column_name='customer', on_delete='CASCADE', lazy_load=False)
    quota = BigIntegerField()   # Quota in bytes.

    @classmethod
    def by_customer(cls, customer: Union[Customer, int]) -> Quota:
        """Returns the settings for the respective customer."""
        return cls.get(cls.customer == customer)

    @property
    def files(self) -> ModelSelect:
        """Yields file records of the respective customer."""
        return File.select(File, FileDBFile).join(FileDBFile).where(
            File.customer == self.customer)

    @property
    def used(self) -> int:
        """Returns used space."""
        return sum(file.size for file in self.files.iterator())

    @property
    def free(self) -> int:
        """Returns free space for the respective customer."""
        return self.quota - self.used

    def alloc(self, size: int) -> bool:
        """Tries to allocate the requested size in bytes."""
        if size > self.free:
            raise QuotaExceeded(quota=self.quota, free=self.free, size=size)

        return True

    def to_json(self, **kwargs) -> dict:
        """Returns a JSON-ish dictionary."""
        json = super().to_json(**kwargs)
        json.update({'free': self.free, 'used': self.used})
        return json
