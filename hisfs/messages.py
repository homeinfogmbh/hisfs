"""Errors of the FS."""

from wsgilib import JSONMessage

__all__ = [
    'NO_SUCH_FILE',
    'FILE_CREATED',
    'FILES_CREATED',
    'FILE_EXISTS',
    'FILE_DELETED',
    'READ_ERROR',
    'QUOTA_EXCEEDED',
    'NOT_A_PDF_DOCUMENT',
    'INVALID_CHUNK_SIZE'
]


NO_SUCH_FILE = JSONMessage('The requested file does not exist.', status=404)
FILE_CREATED = JSONMessage('The file has been created.', status=201)
FILES_CREATED = JSONMessage('The files have been created.', status=200)
FILE_EXISTS = JSONMessage('The file already exists.', status=409)
FILE_DELETED = JSONMessage('The file has been deleted.', status=200)
READ_ERROR = JSONMessage('Could not read file.', status=500)
QUOTA_EXCEEDED = JSONMessage(
    'You have reached your disk space quota.', status=403)
NOT_A_PDF_DOCUMENT = JSONMessage('The file is not a PDF document.', status=400)
CURRUPT_PDF = JSONMessage('The PDF document is currupted.', status=406)
INVALID_CHUNK_SIZE = JSONMessage('Invalid chunk size.', status=400)
