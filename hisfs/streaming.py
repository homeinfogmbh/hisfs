"""File streaming."""

from flask import request, Response

from filedb import NamedFileStream

from hisfs.messages import INVALID_CHUNK_SIZE


__all__ = ['FileStream']


ALLOWED_CHUNK_SIZES = range(4096, 4096 * 1024 * 1024 + 1)


def get_chunk_size():
    """Gets the chunk size from the request args."""

    try:
        chunk_size = request.args['chunk_size']
    except KeyError:
        return min(ALLOWED_CHUNK_SIZES)

    try:
        chunk_size = int(chunk_size)
    except ValueError:
        raise INVALID_CHUNK_SIZE

    if chunk_size in ALLOWED_CHUNK_SIZES:
        return chunk_size

    raise INVALID_CHUNK_SIZE


class FileStream(Response):     # pylint: disable=R0901
    """A stream response."""

    def __init__(self, file, chunk_size=4096):
        """Sets the file, chunk size and status code."""
        stream = NamedFileStream(file.stream, chunk_size=chunk_size)
        super().__init__(stream, mimetype=file.mimetype)

    @classmethod
    def from_request_args(cls, file):
        """Gets the chunk size from the request args."""
        return cls(file, chunk_size=get_chunk_size())
