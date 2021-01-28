"""File management module."""

from logging import INFO, basicConfig
from typing import Callable, Union

from flask import Response, request
from peewee import IntegrityError

from his import CUSTOMER, SESSION, authenticated, authorized, Application
from wsgilib import Binary, JSON, JSONMessage

from hisfs.config import DEFAULT_QUOTA, LOG_FORMAT
from hisfs.exceptions import FileExists
from hisfs.exceptions import QuotaExceeded
from hisfs.exceptions import UnsupportedFileType
from hisfs.functions import get_file, get_files
from hisfs.messages import FILE_CREATED
from hisfs.messages import FILE_DELETED
from hisfs.messages import FILE_EXISTS
from hisfs.messages import FILE_IN_USE
from hisfs.messages import FILES_CREATED
from hisfs.messages import NO_SUCH_FILE
from hisfs.messages import QUOTA_EXCEEDED
from hisfs.messages import READ_ERROR
from hisfs.orm import File, Quota, Thumbnail


__all__ = ['APPLICATION']


APPLICATION = Application('hisfs', debug=True)
DEFAULT_FORMAT = 'png'


def _get_quota() -> Quota:
    """Returns the customer's quota."""

    try:
        return Quota.get(Quota.customer == CUSTOMER.id)
    except Quota.DoesNotExist:
        return Quota(customer=CUSTOMER.id, quota=DEFAULT_QUOTA)


def qalloc(bytec: int) -> bool:
    """Attempts to allocate the respective amount of bytes."""

    try:
        return _get_quota().alloc(bytec)
    except QuotaExceeded:
        raise QUOTA_EXCEEDED from None


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


def with_file(function: Callable) -> Callable:
    """Decorator to translate file ID to an actual file record."""

    def wrapper(ident, *args, **kwargs):
        """Calls the original function with
        the file record as first argument.
        """
        condition = File.id == ident

        if not SESSION.account.root:
            condition &= File.customer == CUSTOMER.id

        try:
            file = get_file(ident)
        except File.DoesNotExist:
            return NO_SUCH_FILE

        return function(file, *args, **kwargs)

    return wrapper


@authenticated
@authorized('hisfs')
def list_() -> JSON:
    """Lists the customer's files."""

    files = get_files(shallow=True).iterator()
    return JSON([file.to_json() for file in files])


@authenticated
@authorized('hisfs')
@with_file
def get(file: File) -> Union[Binary, JSON, Response]:
    """Returns the respective file."""

    file = try_thumbnail(file)

    if 'metadata' in request.args:
        return JSON(file.to_json())

    if 'stream' in request.args:
        return file.stream()

    if 'named' in request.args:
        return Binary(file.bytes, filename=file.name)

    return Binary(file.bytes)


@authenticated
@authorized('hisfs')
def post(name: str) -> JSONMessage:
    """Adds a new file."""

    data = request.get_data()
    rename = 'rename' in request.args
    qalloc(len(data))

    try:
        file = File.add(name, CUSTOMER.id, data, rename=rename)
    except FileExists as file_exists:
        raise FILE_EXISTS.update(id=file_exists.file.id)

    file.save()
    return FILE_CREATED.update(id=file.id)


@authenticated
@authorized('hisfs')
def post_multi() -> JSONMessage:
    """Adds multiple new files."""

    rename = 'rename' in request.args
    created = {}
    existing = {}
    too_large = []
    quota_exceeded = []

    for name, file_storage in request.files.items():
        try:
            data = file_storage.stream.read()
        except MemoryError:
            too_large.append(name)
            continue

        try:
            _get_quota().alloc(len(data))
        except QuotaExceeded:
            quota_exceeded.append(name)
            continue

        try:
            file = File.add(name, CUSTOMER.id, data, rename=rename)
        except FileExists as file_exists:
            file = file_exists.file
            existing[file.name] = file.id
        else:
            file.save()
            created[name] = file.id

    status = 400 if (too_large or quota_exceeded) else 200
    return FILES_CREATED.update(
        created=created, existing=existing, too_large=too_large,
        quota_exceeded=quota_exceeded, status=status)


@authenticated
@authorized('hisfs')
@with_file
def delete(file: File) -> JSONMessage:
    """Deletes the respective file."""

    try:
        file.delete_instance()
    except IntegrityError:
        return FILE_IN_USE

    return FILE_DELETED


@APPLICATION.before_first_request
def init():
    """Initializes the app."""

    basicConfig(level=INFO, format=LOG_FORMAT)


@APPLICATION.errorhandler(FileNotFoundError)
@APPLICATION.errorhandler(PermissionError)
def _handle_read_error(_):
    """Returns a read error message."""

    return READ_ERROR


ROUTES = (
    ('GET', '/', list_),
    ('GET', '/<int:ident>', get),
    ('POST', '/', post_multi),
    ('POST', '/<name>', post),
    ('DELETE', '/<int:ident>', delete)
)
APPLICATION.add_routes(ROUTES)
