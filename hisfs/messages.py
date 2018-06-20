"""Errors of the FS."""

from his.messages import Message

__all__ = [
    'NoSuchFile',
    'FileCreated',
    'FilesCreated',
    'FileExists',
    'FileDeleted',
    'ReadError',
    'QuotaExceeded',
    'NotAPDFDocument']


class HISFSMessage(Message):
    """Indicates errors within the file system."""

    DOMAIN = 'hisfs'


class NoSuchFile(HISFSMessage):
    """Indicates that the respective file does not exist."""

    STATUS = 404


class FileCreated(HISFSMessage):
    """Indicates that the respective file has been created."""

    STATUS = 201


class FilesCreated(HISFSMessage):
    """Indicates that the respective files hve been created."""

    def __init__(self, files, existing, too_large=None, quota_exceeded=None):
        """Sets the respective attributes."""
        super().__init__(
            status=400 if too_large or quota_exceeded else None, files=files,
            existing=existing, too_large=too_large or (),
            quota_exceeded=quota_exceeded or ())


class FileExists(HISFSMessage):
    """Indicates that the respective file already exists."""

    STATUS = 409


class FileDeleted(HISFSMessage):
    """Indicates that the respective file
    has successfully been deleted.
    """

    STATUS = 200


class ReadError(HISFSMessage):
    """Indicates that no data could be read from filedb."""

    STATUS = 500


class QuotaExceeded(HISFSMessage):
    """Indicates that the respective customer has exceeded their quota."""

    STATUS = 403


class NotAPDFDocument(HISFSMessage):
    """Indicates that the respective file is not a PDF document."""

    STATUS = 400
