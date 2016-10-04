"""File system errors definition"""

__all__ = [
    'FileSystemError',
    'NotADirectory',
    'NotAFile',
    'NoSuchNode',
    'ReadError',
    'WriteError',
    'DirectoryNotEmpty']


class FileSystemError(Exception):
    """Indicates errors within the file system"""

    pass


class NotADirectory(FileSystemError):
    """Indicates that an inode is not a
    directory but was expected to be one
    """

    def __init__(self, path):
        super().__init__(path)
        self.path = path


class NotAFile(FileSystemError):
    """Indicates that an inode is not a
    file but was expected to be one
    """

    pass


class NoSuchNode(FileSystemError):
    """Indicates that the respective path node does not exists"""

    def __init__(self, path):
        super().__init__(path)
        self.path = path


class ReadError(FileSystemError):
    """Indicates that no data could be read from filedb"""

    pass


class WriteError(FileSystemError):
    """Indicates that no data could be written to filedb"""

    pass


class DirectoryNotEmpty(FileSystemError):
    """Indicates that the directory could
    not be deleted because it is not empty
    """

    pass
