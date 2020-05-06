"""External functions."""

from his import ACCOUNT, CUSTOMER

from hisfs.messages import NO_SUCH_FILE
from hisfs.orm import File


__all__ = ['get_file', 'file_usage']


def get_file(file_id, *, exception=NO_SUCH_FILE):
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

        raise exception


def file_usage(consistency_error):
    """Returns the file usage from a peewee.ConsistencyError."""

    # TODO: implement.
    pass
