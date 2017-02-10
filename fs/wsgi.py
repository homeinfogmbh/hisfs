"""File management module"""

from os.path import dirname, basename
from contextlib import suppress

from peewee import DoesNotExist

from homeinfo.lib.wsgi import OK, JSON, Binary
from filedb import FileError

from his.api.messages import NotAnInteger
from his.api.handlers import AuthorizedService

from .messages import NotADirectory, NoSuchNode, DeletionError, \
    NoFileNameSpecified, InvalidFileName, FileExists, FileCreated, \
    FileDeleted, FileUnchanged, NotWritable, NotReadable, RootDeletionError, \
    ParentDirDoesNotExist
from .orm import Inode


__all__ = ['FS']


class FS(AuthorizedService):
    """Service that manages files"""

    NODE = 'fs'
    NAME = 'FileSystem'
    DESCRIPTION = 'Dateisystem'
    PROMOTE = False

    @property
    def sha256sum(self):
        """Returns the specified SHA-256 checksum"""
        return self.environ['HTTP_IF_NONE_MATCH']

    @property
    def mode(self):
        """Returns the desired file mode"""
        try:
            mode = self.query['mode']
        except KeyError:
            # Return default modes
            if self.data:
                return 0o644
            else:
                return 0o755
        else:
            try:
                return int(mode)
            except (TypeError, ValueError):
                raise NotAnInteger('mode', mode) from None

    @property
    def recursive(self):
        """Returns the recursive flag"""
        return

    def get(self):
        """Retrieves (a) file(s)"""
        if self.resource is None:
            root = Inode.root_for(owner=self.account, group=self.customer)
            return JSON(root.dict_for(self.account))
        else:
            try:
                inode = Inode.by_path(
                    self.resource,
                    owner=self.account,
                    group=self.group)
            except DoesNotExist:
                raise NoSuchNode() from None
            else:
                if inode.readable_by(self.account):
                    with suppress(KeyError):
                        # Access self.sha256sum first to trigger a possible
                        # KeyError before the resource-hungry inode.sha256sum
                        # is invoked.
                        if self.sha256sum == inode.sha256sum:
                            return FileUnchanged()

                    if self.query.get('sha256sum', False):
                        return OK(inode.sha256sum)
                    else:
                        return Binary(inode.data)
                else:
                    raise NotReadable() from None

    def post(self):
        """Adds new files"""
        if self.resource is None:
            raise NoFileNameSpecified()
        else:
            try:
                Inode.by_path(
                    self.resource,
                    owner=self.account,
                    group=self.group)
            except DoesNotExist:
                parent = dirname(self.resource)

                try:
                    parent = Inode.by_path(
                        parent,
                        owner=self.account,
                        group=self.group)
                except DoesNotExist:
                    raise ParentDirDoesNotExist() from None
                else:
                    if parent.isdir:
                        if parent.writable_by(self.account):
                            inode = Inode()

                            try:
                                inode.name = basename(self.resource)
                            except ValueError:
                                raise InvalidFileName()
                            else:
                                inode.owner = self.account
                                inode.group = self.customer
                                inode.parent = parent

                                if self.data:
                                    inode.data = self.data

                                inode.mode = self.mode
                                inode.save()
                                return FileCreated()
                        else:
                            raise NotWritable() from None
                    else:
                        raise NotADirectory() from None
            else:
                raise FileExists() from None

    def delete(self):
        """Deletes a file"""
        if self.resource is None:
            raise NoFileNameSpecified()
        else:
            try:
                inode = Inode.by_path(
                    self.resource,
                    owner=self.account,
                    group=self.group)
            except DoesNotExist:
                raise NoSuchNode() from None
            else:
                if inode.parent is None:
                    raise RootDeletionError() from None
                else:
                    if inode.parent.writable_by(self.account):
                        try:
                            inode.remove(recursive=self.query.get(
                                'recursive', False))
                        except FileError:
                            raise DeletionError() from None
                        else:
                            return FileDeleted()
                    else:
                        raise NotWritable() from None

    def options(self):
        """Returns options information"""
        return OK()
