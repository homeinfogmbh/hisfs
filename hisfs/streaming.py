"""File streaming."""

from flask import request, Response

from hisfs.messages import INVALID_CHUNK_SIZE


__all__ = ['FileStream']


MIN_CHUNK_SIZE = 4096
DEFAULT_CHUNK_SIZE = MIN_CHUNK_SIZE * 1024
MAX_CHUNK_SIZE = DEFAULT_CHUNK_SIZE * 1024
ALLOWED_CHUNK_SIZES = range(MIN_CHUNK_SIZE, MAX_CHUNK_SIZE)


def get_chunk_size():
    """Gets the chunk size from the request args."""

    try:
        chunk_size = request.args['chunk_size']
    except KeyError:
        return DEFAULT_CHUNK_SIZE

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
        super().__init__(
            file.stream(chunk_size), mimetype=file.mimetype,
            content_type=file.mimetype, direct_passthrough=True)
        self.headers.add('Content-Length', file.size)

    @classmethod
    def from_request_args(cls, file):
        """Gets the chunk size from the request args."""
        return cls(file, chunk_size=get_chunk_size())
