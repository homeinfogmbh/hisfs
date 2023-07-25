"""File management module."""

from logging import INFO, basicConfig
from typing import Callable, Union

from flask import Response, request
from peewee import DataError, IntegrityError

from his import CUSTOMER, SESSION, authenticated, authorized, Application
from wsgilib import Binary, JSON, JSONMessage, get_bool

from hisfs.config import LOG_FORMAT
from hisfs.errors import ERRORS
from hisfs.exceptions import FileExists
from hisfs.exceptions import QuotaExceeded
from hisfs.functions import get_file, get_files, qalloc, try_thumbnail
from hisfs.orm import File


__all__ = ["APPLICATION"]


APPLICATION = Application("hisfs", debug=True)
DEFAULT_FORMAT = "png"


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
@authorized("hisfs")
def list_() -> JSON:
    """Lists the customer's files."""

    files = get_files(shallow=True).iterator()
    return JSON([file.to_json() for file in files])


@authenticated
@authorized("hisfs")
@with_file
def get(file: File) -> Union[Binary, JSON, Response]:
    """Returns the respective file."""

    file = try_thumbnail(file)

    if "metadata" in request.args:
        return JSON(file.to_json())

    if "stream" in request.args:
        return file.stream()

    if "named" in request.args:
        return Binary(file.bytes, filename=file.name)

    return Binary(file.bytes)


@authenticated
@authorized("hisfs")
def post(name: str) -> JSONMessage:
    """Adds a new file."""

    data = request.get_data()
    qalloc(len(data))
    file = File.add(name, CUSTOMER.id, data, rename=get_bool("rename"))
    file.save()
    return JSONMessage("The file has been created.", id=file.id, status=201)


@authenticated
@authorized("hisfs")
def post_multi() -> JSONMessage:
    """Adds multiple new files."""

    rename = get_bool("rename")
    created = {}
    existing = {}
    too_large = []
    data_errors = {}
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
            existing[file_exists.file.name] = file_exists.file.id
            continue

        try:
            file.save()
        except DataError as data_error:
            data_errors[name] = data_error.args
            continue

        created[name] = file.id

    status = 400 if any([too_large, quota_exceeded, data_errors]) else 200
    return JSONMessage(
        "The files have been created.",
        created=created,
        existing=existing,
        too_large=too_large,
        data_errors=data_errors,
        quota_exceeded=quota_exceeded,
        status=status,
    )


@authenticated
@authorized("hisfs")
@with_file
def delete(file: File) -> JSONMessage:
    """Deletes the respective file."""

    try:
        file.delete_instance()
    except IntegrityError:
        return JSONMessage("The file is currently in use.", status=423)

    return JSONMessage("The file has been deleted.", status=200)


@APPLICATION.before_first_request
def init():
    """Initializes the app."""

    basicConfig(level=INFO, format=LOG_FORMAT)


ROUTES = (
    ("GET", "/", list_),
    ("GET", "/<int:ident>", get),
    ("POST", "/", post_multi),
    ("POST", "/<name>", post),
    ("DELETE", "/<int:ident>", delete),
)
APPLICATION.add_routes(ROUTES)
APPLICATION.register_error_handlers(ERRORS)
