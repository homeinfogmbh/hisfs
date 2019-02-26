"""File streaming."""

from filedb import NamedFileStream as _NamedFileStream


__all__ = ['NamedFileStream']


class NamedFileStream(_NamedFileStream):
    """Extension of the filedb.NamedFileStream."""

    @classmethod
    def from_hisfs(cls, file, *, chunk_size=4096):
        """Creates a file stream from a hisfs.File."""
        return cls(file.stream, chunk_size=chunk_size)
