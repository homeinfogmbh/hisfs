"""External functions."""

from his import ACCOUNT, CUSTOMER

from hisfs.orm import File


__all__ = ['check_file_access']


def check_file_access(file_id):
    """Checks the persmissions of the file access."""

    condition = File.id == file_id

    if not ACCOUNT.root:
        condition &= File.customer == CUSTOMER.id

    return File.get(condition)
