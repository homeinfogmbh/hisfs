"""External functions."""

from typing import Union

from flask import request
from peewee import ModelSelect

from his import CUSTOMER

from hisfs.config import get_config
from hisfs.exceptions import UnsupportedFileType
from hisfs.orm import File, Quota, Thumbnail


__all__ = ['get_file', 'get_files', 'get_quota', 'qalloc', 'try_thumbnail']


def get_files(shallow: bool = True) -> ModelSelect:
    """Selects files."""

    return File.select(cascade=True, shallow=shallow).where(
        File.customer == CUSTOMER.id)


def get_file(file_id: Union[int, File]) -> File:
    """Returns a file by its ID with permission checks."""

    return get_files(shallow=False).where(File.id == file_id).get()


def get_quota() -> Quota:
    """Returns the customer's quota."""

    try:
        return Quota.get(Quota.customer == CUSTOMER.id)
    except Quota.DoesNotExist:
        return Quota(customer=CUSTOMER.id,
                     quota=get_config().getint('fs', 'quota'))


def qalloc(bytec: int) -> bool:
    """Attempts to allocate the respective amount of bytes."""

    return get_quota().alloc(bytec)


def try_thumbnail(file: File) -> Union[File, Thumbnail]:
    """Attempts to return a thumbnail if desired."""

    try:
        resolution = request.args['thumbnail']
    except KeyError:
        return file

    size_x, size_y = resolution.split('x')
    resolution = (int(size_x), int(size_y))

    try:
        return file.thumbnail(resolution)
    except UnsupportedFileType:
        return file
