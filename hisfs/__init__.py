"""HIS module providing a file system."""

from hisfs.functions import get_file, file_usage
from hisfs.orm import File


__all__ = ['get_file', 'file_usage', 'File']
