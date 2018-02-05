"""File management module."""

from flask import request

from his import ACCOUNT, CUSTOMER, DATA, authenticated, authorized, Account
from wsgilib import Application, JSON, Binary

from hisfs.messages import QuotaUnconfigured, NoSuchFile, FileCreated, \
    FilePatched, FileDeleted
from hisfs.orm import File, CustomerQuota


__all__ = ['APPLICATION']


APPLICATION = Application('hisfs', cors=True, debug=True)


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

    try:
        quota = CustomerQuota.get(CustomerQuota.customer == CUSTOMER.id)
    except CustomerQuota.DoesNotExist:
        raise QuotaUnconfigured()

    quota.alloc(len(data))  # Raises QuotaExceeded() on failure.
    file = File.add(name, ACCOUNT.id, data)
    file.save()
    return FileCreated(id=file.id)


@authenticated
@authorized('hisfs')
def patch(ident):
    """Modifies the respective file."""

    _get_file(ident).patch(DATA.json)
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
    ('POST', '/<name>', post, 'post_file'),
    ('PATCH', '/<int:ident>', patch, 'patch_file'),
    ('DELETE', '/<int:ident>', delete, 'delete_file'))
APPLICATION.add_routes(ROUTES)
