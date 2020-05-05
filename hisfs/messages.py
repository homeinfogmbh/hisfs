"""Errors of the FS."""

from wsgilib import JSONMessage

__all__ = [
    'NO_SUCH_FILE',
    'FILE_CREATED',
    'FILES_CREATED',
    'FILE_EXISTS',
    'FILE_DELETED',
    'FILE_IN_USE',
    'READ_ERROR',
    'QUOTA_EXCEEDED'
]


NO_SUCH_FILE = JSONMessage('The requested file does not exist.', status=404)
FILE_CREATED = JSONMessage('The file has been created.', status=201)
FILES_CREATED = JSONMessage('The files have been created.', status=200)
FILE_EXISTS = JSONMessage('The file already exists.', status=409)
FILE_DELETED = JSONMessage('The file has been deleted.', status=200)
FILE_IN_USE = JSONMessage('The file is currently in use.', status=423)
READ_ERROR = JSONMessage('Could not read file.', status=500)
QUOTA_EXCEEDED = JSONMessage(
    'You have reached your disk space quota.', status=403)
