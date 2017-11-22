"""Errors of the FS."""

from his.api.messages import locales, HISMessage

__all__ = [
    'FileSystemError',
    'NotADirectory',
    'NotAFile',
    'NoSuchNode',
    'ParentDirDoesNotExist',
    'ReadError',
    'WriteError',
    'DirectoryNotEmpty',
    'DeletionError',
    'NoFileNameSpecified',
    'NoInodeSpecified',
    'InvalidFileName',
    'NoDataProvided',
    'FileExists',
    'FileCreated',
    'FileUpdated',
    'FileDeleted',
    'FileUnchanged',
    'NotExecutable',
    'NotWritable',
    'NotReadable',
    'RootDeletionError',
    'QuotaExceeded']


@locales('/etc/his.d/locale/fs.ini')
class FileSystemError(HISMessage):
    """Indicates errors within the file system."""

    pass


class NotADirectory(FileSystemError):
    """Indicates that an inode is not a
    directory but was expected to be one.
    """

    STATUS = 406


class NotAFile(FileSystemError):
    """Indicates that an inode is not a
    file but was expected to be one.
    """

    STATUS = 406


class NoSuchNode(FileSystemError):
    """Indicates that the respective path node does not exist."""

    STATUS = 404


class ParentDirDoesNotExist(FileSystemError):
    """Indicates that the requested node's parent does not exist."""

    STATUS = 404


class ReadError(FileSystemError):
    """Indicates that no data could be read from filedb."""

    STATUS = 500


class WriteError(FileSystemError):
    """Indicates that no data could be written to filedb."""

    STATUS = 500


class DirectoryNotEmpty(FileSystemError):
    """Indicates that the directory could
    not be deleted because it is not empty.
    """

    STATUS = 400


class DeletionError(FileSystemError):
    """Indicates that an inode could not be deleted."""

    STATUS = 500


class NoFileNameSpecified(HISMessage):
    """Indicates that no file name was provided."""

    STATUS = 400


class NoInodeSpecified(HISMessage):
    """Indicates that no Inode provided."""

    STATUS = 400


class InvalidFileName(HISMessage):
    """Indicates that the given file name is invalid."""

    STATUS = 400


class NoDataProvided(HISMessage):
    """Indicates that no data has been provided."""

    STATUS = 400


class FileExists(HISMessage):
    """Indicates that the file already exists."""

    STATUS = 409


class FileCreated(HISMessage):
    """Indicates that the file was successfully created."""

    STATUS = 201


class FileUpdated(HISMessage):
    """Indicates that the file was successfully updated."""

    STATUS = 200


class FileDeleted(HISMessage):
    """Indicates that the file was successfully deleted."""

    STATUS = 200


class FileUnchanged(HISMessage):
    """Indicates that the file was not changed."""

    STATUS = 200


class NotExecutable(HISMessage):
    """Indicates that the inode is not executable."""

    STATUS = 403


class NotWritable(HISMessage):
    """Indicates that the inode is not writable."""

    STATUS = 403


class NotReadable(HISMessage):
    """Indicates that the inode is not writable."""

    STATUS = 403


class RootDeletionError(HISMessage):
    """Indicates that the root inode was attempted to be deleted."""

    STATUS = 403


class QuotaExceeded(HISMessage):
    """Indicates that the customer's quota has been exceeded."""

    status = 403
