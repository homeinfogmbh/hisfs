"""Errors of the FS."""

from his import HIS_MESSAGE_FACILITY

__all__ = [
    'NO_SUCH_FILE',
    'FILE_CREATED',
    'FILES_CREATED',
    'FILE_EXISTS',
    'FILE_DELETED',
    'READ_ERROR',
    'QUOTA_EXCEEDED',
    'NOT_A_PDF_DOCUMENT']


HISFS_MESSAGE_DOMAIN = HIS_MESSAGE_FACILITY.domain('hisfs')
HISFS_MESSAGE = HISFS_MESSAGE_DOMAIN.message
NO_SUCH_FILE = HISFS_MESSAGE('The requested file does not exist.', status=404)
FILE_CREATED = HISFS_MESSAGE('The file has been created.', status=201)
FILES_CREATED = HISFS_MESSAGE('The files have been created.', status=200)
FILE_EXISTS = HISFS_MESSAGE('The file already exists.', status=409)
FILE_DELETED = HISFS_MESSAGE('The file has been deleted.', status=200)
READ_ERROR = HISFS_MESSAGE('Could not read file.', status=500)
QUOTA_EXCEEDED = HISFS_MESSAGE(
    'You have reached your disk space quota.', status=403)
NOT_A_PDF_DOCUMENT = HISFS_MESSAGE(
    'The file is not a PDF document.', status=400)
