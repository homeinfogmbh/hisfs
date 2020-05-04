"""External functions."""

from his import ACCOUNT, CUSTOMER

from hisfs.orm import File


__all__ = ['get_file']


def get_file(file_id):
    """Returns a file by its ID with permission checks."""

    condition = File.id == file_id

    if not ACCOUNT.root:
        condition &= File.customer == CUSTOMER.id

    return File.get(condition)
