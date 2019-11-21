"""File streaming."""

from flask import Response


__all__ = ['stream']


def stream(file):
    """Creates a file stream."""

    response = Response(
        file.stream, mimetype=file.mimetype, content_type=file.mimetype,
        direct_passthrough=True)
    response.headers.add('content-length', file.size)
    return response
