"""File streaming."""

from flask import Response

from filedb import get


__all__ = ['stream']


def stream(file):
    """Creates a file stream."""

    stream_ = get(file.id, stream=True)
    response = Response(
        stream_, mimetype=file.mimetype, content_type=file.mimetype,
        direct_passthrough=True)
    response.headers.add('content-length', file.size)
    return response
