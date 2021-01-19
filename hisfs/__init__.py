"""HIS module providing a file system."""

from hisfs.exceptions import QuotaExceeded
from hisfs.functions import get_file
from hisfs.orm import File


__all__ = ['QuotaExceeded', 'get_file', 'File']
