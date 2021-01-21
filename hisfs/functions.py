"""External functions."""

from typing import Union

from peewee import ModelSelect

from his import ACCOUNT, CUSTOMER

from hisfs.messages import NO_SUCH_FILE
from hisfs.orm import File


__all__ = ['get_file', 'get_files']


def get_files() -> ModelSelect:
    """Selects files."""

    condition = True

    if not ACCOUNT.root:
        condition &= File.customer == CUSTOMER.id

    return File.select(cascade=True).where(condition)


def get_file(file_id: Union[int, File], *,
             exception: Exception = NO_SUCH_FILE) -> File:
    """Returns a file by its ID with permission checks."""

    if file_id is None:
        return None

    try:
        return get_files().where(File.id == file_id).get()
    except File.DoesNotExist:
        if exception is None:
            raise

        raise exception from None
