"""Errors of the FS."""

from his.messages import locales, Message

__all__ = [
    'FileSystemError',
    'NoSuchFile',
    'FileCreated',
    'FileExists',
    'FileDeleted',
    'ReadError',
    'QuotaExceeded',
    'NotAPDFDocument']


class FileSystemError(Message):
    """Indicates errors within the file system."""

    LOCALES = locales('/etc/his.d/locale/fs.ini')
    ABSTRACT = True


class NoSuchFile(FileSystemError):
    """Indicates that the respective file does not exist."""

    STATUS = 404


class FileCreated(FileSystemError):
    """Indicates that the respective file has been created."""

    STATUS = 201


class FileExists(FileSystemError):
    """Indicates that the respective file already exists."""

    STATUS = 409


class FileDeleted(FileSystemError):
    """Indicates that the respective file
    has successfully been deleted.
    """

    STATUS = 200


class ReadError(FileSystemError):
    """Indicates that no data could be read from filedb."""

    STATUS = 500


class QuotaExceeded(FileSystemError):
    """Indicates that the respective customer has exceeded their quota."""

    STATUS = 403


class NotAPDFDocument(FileSystemError):
    """Indicates that the respective file is not a PDF document."""

    STATUS = 400
