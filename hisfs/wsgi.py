"""File management module."""

from logging import INFO, basicConfig
from typing import Callable, Union

from flask import Response, request
from peewee import IntegrityError

from his import CUSTOMER, SESSION, authenticated, authorized, Application
from wsgilib import Binary, JSON, JSONMessage

from hisfs.config import LOG_FORMAT
from hisfs.exceptions import FileExists
from hisfs.exceptions import QuotaExceeded
from hisfs.functions import get_file, get_files, qalloc, try_thumbnail
from hisfs.orm import File


__all__ = ['APPLICATION']


APPLICATION = Application('hisfs', debug=True)
DEFAULT_FORMAT = 'png'


def with_file(function: Callable) -> Callable:
    """Decorator to translate file ID to an actual file record."""

    def wrapper(ident, *args, **kwargs):
        """Calls the original function with
        the file record as first argument.
        """
        condition = File.id == ident

        if not SESSION.account.root:
            condition &= File.customer == CUSTOMER.id

        file = get_file(ident)
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
    file = File.add(name, CUSTOMER.id, data, rename=rename)
    file.save()
    return JSONMessage('The file has been created.', id=file.id, status=201)


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
            qalloc(len(data))
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
    return JSONMessage('The files have been created.', created=created,
                       existing=existing, too_large=too_large,
                       quota_exceeded=quota_exceeded, status=status)


@authenticated
@authorized('hisfs')
@with_file
def delete(file: File) -> JSONMessage:
    """Deletes the respective file."""

    file.delete_instance()
    return JSONMessage('The file has been deleted.', status=200)


@APPLICATION.before_first_request
def init():
    """Initializes the app."""

    basicConfig(level=INFO, format=LOG_FORMAT)


@APPLICATION.errorhandler(File.DoesNotExist)
def _handle_non_existant_file(_: File.DoesNotExist):
    """Handles non-existant files."""

    return JSONMessage('No such file.', status=404)


@APPLICATION.errorhandler(QuotaExceeded)
def _handle_quota_exceeded(_: QuotaExceeded):
    """Handles exceeded quotas."""

    return JSONMessage('You have reached your disk space quota.', status=403)


@APPLICATION.errorhandler(FileExists)
def _handle_file_exists(error: FileExists):
    """Handles file exists errors."""

    return JSONMessage('The file already exists.', id=error.file.id,
                       status=409)


@APPLICATION.errorhandler(IntegrityError)
def _handle_integrity_error(_: IntegrityError):
    """Handles intetrity errors."""

    return JSONMessage('The file is currently in use.', status=423)


ROUTES = (
    ('GET', '/', list_),
    ('GET', '/<int:ident>', get),
    ('POST', '/', post_multi),
    ('POST', '/<name>', post),
    ('DELETE', '/<int:ident>', delete)
)
APPLICATION.add_routes(ROUTES)
