"""File management module."""

from flask import request
from werkzeug.local import LocalProxy

from his import CUSTOMER, authenticated, authorized
from wsgilib import Application, JSON, Binary

from hisfs.config import DEFAULT_QUOTA
from hisfs.messages import NoSuchFile, FileCreated, FileExists, FileDeleted, \
    QuotaExceeded
from hisfs.orm import File, CustomerQuota


__all__ = ['APPLICATION']


APPLICATION = Application('hisfs', cors=True, debug=True)


def _get_quota():
    """Returns the customer's quota."""

    try:
        return CustomerQuota.get(CustomerQuota.customer == CUSTOMER.id)
    except CustomerQuota.DoesNotExist:
        return CustomerQuota(customer=CUSTOMER.id, quota=DEFAULT_QUOTA)


QUOTA = LocalProxy(_get_quota)


def with_file(function):
    """Decorator to translate file ID to actual file."""

    def wrapper(ident, *args, **kwargs):
        """Wraps the function."""
        try:
            file = File.select().where(
                (File.id == ident) & (File.customer == CUSTOMER.id)).get()
        except File.DoesNotExist:
            raise NoSuchFile()

        return function(file, *args, **kwargs)

    return wrapper


@authenticated
@authorized('hisfs')
def list_():
    """Lists the respective files."""

    return JSON([file.to_dict() for file in File.select().where(
        File.customer == CUSTOMER.id)])


@authenticated
@authorized('hisfs')
@with_file
def get(file):
    """Returns the respective file."""

    if 'metadata' in request.args:
        return JSON(file.to_dict())
    elif 'named' in request.args:
        return Binary(file.data, filename=file.name)

    return Binary(file.data)


@authenticated
@authorized('hisfs')
def post(name):
    """Adds a new file."""

    data = request.get_data()
    QUOTA.alloc(len(data))
    file = File.add(name, CUSTOMER.id, data)
    file.save()
    return FileCreated(id=file.id)


@authenticated
@authorized('hisfs')
def post_multi():
    """Adds a new files."""

    added = {}
    existing = []
    too_large = []
    quota_exceeded = []

    for name, file_storage in request.files.items():
        try:
            data = file_storage.stream.read()
        except MemoryError:
            too_large.append(name)
            continue

        try:
            QUOTA.alloc(len(data))
        except QuotaExceeded:
            quota_exceeded.append(name)
            continue

        try:
            file = File.add(name, CUSTOMER.id, data)
        except FileExists:
            existing.append(name)
            continue

        file.save()
        added[name] = file.id

    status = 400 if existing or too_large or quota_exceeded else 201
    return JSON({
        'added': added, 'existing': existing, 'too_large': too_large,
        'quota_exceeded': quota_exceeded}, status=status)


@authenticated
@authorized('hisfs')
@with_file
def delete(file):
    """Deletes the respective file."""

    file.delete_instance()
    return FileDeleted()


ROUTES = (
    ('GET', '/', list_, 'list_files'),
    ('GET', '/<int:ident>', get, 'get_file'),
    ('POST', '/', post_multi, 'post_files'),
    ('POST', '/<name>', post, 'post_file'),
    ('DELETE', '/<int:ident>', delete, 'delete_file'))
APPLICATION.add_routes(ROUTES)
