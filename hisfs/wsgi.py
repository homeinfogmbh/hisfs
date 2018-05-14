"""File management module."""

from flask import request
from werkzeug.local import LocalProxy

from his import ACCOUNT, CUSTOMER, DATA, authenticated, authorized, Account
from wsgilib import Application, JSON, Binary

from hisfs.messages import QuotaUnconfigured, NoSuchFile, FileCreated, \
    FileExists, FilePatched, FileDeleted, QuotaExceeded
from hisfs.orm import File, CustomerQuota


__all__ = ['APPLICATION']


APPLICATION = Application('hisfs', cors=True, debug=True)


def _get_quota():
    """Returns the customer's quota."""

    try:
        return CustomerQuota.get(CustomerQuota.customer == CUSTOMER.id)
    except CustomerQuota.DoesNotExist:
        raise QuotaUnconfigured()


QUOTA = LocalProxy(_get_quota)


def _list_files():
    """Lists the files of the current customer."""

    return File.select().join(Account).where(Account.customer == CUSTOMER.id)


def _get_file(ident):
    """Returns the file with the respective id of the current customer."""

    try:
        return File.select().join(Account).where(
            (File.id == ident) & (Account.customer == CUSTOMER.id)).get()
    except File.DoesNotExist:
        raise NoSuchFile()


@authenticated
@authorized('hisfs')
def list_():
    """Lists the respective files."""

    return JSON([file.to_dict() for file in _list_files()])


@authenticated
@authorized('hisfs')
def get(ident):
    """Returns the respective file."""

    try:
        request.args['metadata']
    except KeyError:
        return Binary(_get_file(ident).data)

    return JSON(_get_file(ident).to_dict())


@authenticated
@authorized('hisfs')
def post(name):
    """Adds a new file."""

    data = DATA.bytes
    QUOTA.alloc(len(data))
    file = File.add(name, ACCOUNT.id, data)
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
            file = File.add(name, ACCOUNT.id, data)
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
def patch(ident):
    """Modifies the respective file."""

    file = _get_file(ident)
    file = file.patch(DATA.json)
    file.save()
    return FilePatched()


@authenticated
@authorized('hisfs')
def delete(ident):
    """Deletes the respective file."""

    _get_file(ident).delete_instance()
    return FileDeleted()


ROUTES = (
    ('GET', '/', list_, 'list_files'),
    ('GET', '/<int:ident>', get, 'get_file'),
    ('POST', '/', post_multi, 'post_files'),
    ('POST', '/<name>', post, 'post_file'),
    ('PATCH', '/<int:ident>', patch, 'patch_file'),
    ('DELETE', '/<int:ident>', delete, 'delete_file'))
APPLICATION.add_routes(ROUTES)
