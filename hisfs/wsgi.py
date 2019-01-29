"""File management module."""

from pathlib import Path

from flask import request

from his import CUSTOMER, SESSION, authenticated, authorized, Application
from wsgilib import JSON, Binary

from hisfs.config import DEFAULT_QUOTA
from hisfs.exceptions import FileExists
from hisfs.exceptions import QuotaExceeded
from hisfs.exceptions import ReadError
from hisfs.exceptions import UnsupportedFileType
from hisfs.hooks import run_delete_hooks
from hisfs.messages import FILE_CREATED
from hisfs.messages import FILE_DELETED
from hisfs.messages import FILE_EXISTS
from hisfs.messages import FILES_CREATED
from hisfs.messages import NO_SUCH_FILE
from hisfs.messages import NOT_A_PDF_DOCUMENT
from hisfs.messages import QUOTA_EXCEEDED
from hisfs.messages import READ_ERROR
from hisfs.orm import File, Quota
from hisfs.util import is_pdf, pdfimages


__all__ = ['APPLICATION']


APPLICATION = Application('hisfs', debug=True)


def _get_quota():
    """Returns the customer's quota."""

    try:
        return Quota.get(Quota.customer == CUSTOMER.id)
    except Quota.DoesNotExist:
        return Quota(customer=CUSTOMER.id, quota=DEFAULT_QUOTA)


def qalloc(bytec):
    """Attempts to allocate the respective amount of bytes."""

    try:
        return _get_quota().alloc(bytec)
    except QuotaExceeded:
        raise QUOTA_EXCEEDED


def try_thumbnail(file):
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


def with_file(function):
    """Decorator to translate file ID to an actual file record."""

    def wrapper(ident, *args, **kwargs):
        """Calls the original function with
        the file record as first argument.
        """
        condition = File.id == ident

        if not SESSION.account.root:
            condition &= File.customer == CUSTOMER.id

        try:
            file = File.get(condition)
        except File.DoesNotExist:
            return NO_SUCH_FILE

        return function(file, *args, **kwargs)

    return wrapper


@authenticated
@authorized('hisfs')
def list_():
    """Lists the customer's files."""

    return JSON([file.to_json() for file in File.select().where(
        File.customer == CUSTOMER.id)])


@authenticated
@authorized('hisfs')
@with_file
def get(file):
    """Returns the respective file."""

    file = try_thumbnail(file)

    if 'metadata' in request.args:
        return JSON(file.to_json())

    if 'named' in request.args:
        return Binary(file.bytes, filename=file.name)

    return Binary(file.bytes)


@authenticated
@authorized('hisfs')
def post(name):
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
def post_multi():
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
def delete(file):
    """Deletes the respective file."""

    run_delete_hooks(file.id)
    file.delete_instance()
    return FILE_DELETED


@authenticated
@authorized('hisfs')
@with_file
def convert_pdf(file):
    """Converts a PDF document into image files."""

    blob = file.bytes

    if not is_pdf(blob):
        raise NOT_A_PDF_DOCUMENT

    format_ = request.args.get('format', 'jpeg')
    suffix = '.{}'.format(format_.lower())
    created = {}
    existing = {}

    for index, blob in enumerate(pdfimages(blob, suffix=suffix)):
        qalloc(len(blob))
        path = Path(file.name)
        name = path.stem + '-page{}'.format(index) + suffix

        try:
            file = File.add(name, CUSTOMER.id, blob)
        except FileExists as file_exists:
            file = file_exists.file
            existing[file.name] = file.id
        else:
            file.save()
            created[name] = file.id

    return FILES_CREATED.update(created=created, existing=existing)


@APPLICATION.errorhandler(ReadError)
def _handle_read_error(_):
    """Returns a read error message."""

    return READ_ERROR


ROUTES = (
    ('GET', '/', list_, 'list_files'),
    ('GET', '/<int:ident>', get, 'get_file'),
    ('POST', '/', post_multi, 'post_files'),
    ('POST', '/<name>', post, 'post_file'),
    ('PATCH', '/<int:ident>', convert_pdf, 'convert_pdf'),
    ('DELETE', '/<int:ident>', delete, 'delete_file'))
APPLICATION.add_routes(ROUTES)
