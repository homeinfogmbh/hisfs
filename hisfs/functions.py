"""External functions."""

from typing import Union

from his import ACCOUNT, CUSTOMER

from hisfs.messages import NO_SUCH_FILE
from hisfs.orm import File


__all__ = ['get_file']


def get_file(file_id: Union[int, File], *,
             exception: Exception = NO_SUCH_FILE) -> File:
    """Returns a file by its ID with permission checks."""

    if file_id is None:
        return None

    condition = File.id == file_id

    if not ACCOUNT.root:
        condition &= File.customer == CUSTOMER.id

    try:
        return File.get(condition)
    except File.DoesNotExist:
        if exception is None:
            raise

        raise exception from None
