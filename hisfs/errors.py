"""Common errors."""

from peewee import IntegrityError

from wsgilib import JSONMessage

from hisfs.exceptions import FileExists, UnsupportedFileType, QuotaExceeded
from hisfs.orm import File


__all__ = ['ERRORS']


ERRORS = {
    File.DoesNotExist: lambda _: JSONMessage('No such file.', status=404),
    FileExists: lambda error: JSONMessage(
        'The file already exists.', id=error.file.id, status=409),
    UnsupportedFileType: lambda _: JSONMessage(
        'Unsupported file type.', status=400),
    QuotaExceeded: lambda _: JSONMessage(
        'You have reached your disk space quota.', status=403),
    IntegrityError: lambda _: JSONMessage(
        'The file is currently in use.', status=423)
}
