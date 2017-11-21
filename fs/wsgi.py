"""File management module."""

from os.path import dirname, basename
from contextlib import suppress

from peewee import DoesNotExist

from wsgilib import OK, JSON, Binary
from filedb import FileError

from his.api.messages import NotAnInteger
from his.api.handlers import service, AuthorizedService

from .messages import NotADirectory, NoSuchNode, DeletionError, \
    NoFileNameSpecified, InvalidFileName, FileExists, FileCreated, \
    FileDeleted, FileUnchanged, NotWritable, NotReadable, RootDeletionError, \
    ParentDirDoesNotExist
from .orm import Inode


__all__ = ['FS']


@service('fs')
@routed('/fs/[id:int]')
class FS(AuthorizedService):
    """Service that manages files."""

    @property
    def path(self):
        """Returns the optional path."""
        try:
            return self.query['path']
        except KeyError:
            raise NoFileNameSpecified()

    @property
    @lru_cache(maxsize=1)
    def inode(self):
        """Returns the requested Inode."""
        if self.vars['id'] is None:
            try:
                return Inode.by_path(
                    self.path, owner=self.account, group=self.customer)
            except NoFileNameSpecified:
                raise NoInodeSpecified() from None
            except DoesNotExist:
                raise NoSuchNode() from None

        try:
            return Inode.by_id(
                self.vars['id'], owner=self.account, group=self.customer)
        except DoesNotExist:
            raise NoSuchNode() from None

    @property
    @lru_cache(maxsize=1)
    def parent(self):
        """Returns the parent inode."""
        try:
            return self.inode
        except NoInodeSpecified:
            return None
        except NoSuchNode:
            raise ParentDirDoesNotExist() from None

    @property
    def sha256sum(self):
        """Returns the specified SHA-256 checksum."""
        return self.environ['HTTP_IF_NONE_MATCH']

    @property
    def mode(self):
        """Returns the desired file mode"""
        try:
            mode = self.query['mode']
        except KeyError:
            # Return default modes.
            if self.data.bytes:
                return 0o644

            return 0o755

        try:
            return int(mode)
        except (TypeError, ValueError):
            raise NotAnInteger('mode', mode) from None

    @property
    def recursive(self):
        """Returns the recursive flag."""
        return

    def root(self):
        """Yields root directory contents."""
        return Inode.root_for(owner=self.account, group=self.customer)

    def list_root(self):
        """Lists the root directoy."""
        return JSON([inode.dict_for(self.account) for inode in self.root])

    def add(self):
        """Adds a new inode."""
        inode = Inode()

        try:
            inode.name = self.name
        except ValueError:
            raise InvalidFileName()

        inode.owner = self.account
        inode.group = self.customer
        inode.parent = self.parent

        if self.data.bytes:
            inode.data = self.data.bytes

        inode.mode = self.mode
        inode.save()
        return FileCreated()

    def get(self):
        """Retrieves (a) file(s)."""
        if self.vars['id'] is None:
            return self.list_root()

        if inode.readable_by(self.account):
            with suppress(KeyError):
                # Access self.sha256sum first to trigger a possible
                # KeyError before the resource-hungry inode.sha256sum
                # is invoked.
                if self.sha256sum == inode.sha256sum:
                    return FileUnchanged()

            if self.query.get('sha256sum', False):
                return OK(inode.sha256sum)

            return Binary(inode.data)

        raise NotReadable() from None

    def post(self):
        """Adds new files."""
        if self.parent.isdir:
            if self.parent.writable_by(self.account):
                if self.name in (child.name for child in self.parent.children):
                    raise FileExists() from None

                return self.add()

            raise NotWritable() from None

        raise NotADirectory() from None

    def delete(self):
        """Deletes a file."""
        if self.resource is None:
            raise NoFileNameSpecified()

        try:
            inode = Inode.by_path(
                self.resource, owner=self.account, group=self.group)
        except DoesNotExist:
            raise NoSuchNode() from None

        if inode.parent is None:
            raise RootDeletionError() from None

        if inode.parent.writable_by(self.account):
            try:
                inode.remove(recursive=self.query.get('recursive', False))
            except FileError:
                raise DeletionError() from None

            return FileDeleted()

        raise NotWritable() from None

    def options(self):
        """Returns options information."""
        return OK()
