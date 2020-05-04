"""HIS module providing a file system."""

from hisfs.functions import check_file_access
from hisfs.orm import File


__all__ = ['check_file_access', 'File']
