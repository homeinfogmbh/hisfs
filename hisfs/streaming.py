"""File streaming."""

from flask import Response

from filedb import NamedFileStream


__all__ = ['FileStream']


class FileStream(Response):     # pylint: disable=R0901
    """A stream response."""

    def __init__(self, file, chunk_size=4096):
        """Sets the file, chunk size and status code."""
        stream = NamedFileStream(file.stream, chunk_size=chunk_size)
        super().__init__(stream, mimetype=file.mimetype)
