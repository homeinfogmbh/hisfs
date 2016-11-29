"""File management module"""

from os.path import dirname, basename
from contextlib import suppress

from homeinfo.lib.wsgi import OK, JSON, Binary
from filedb import FileError

from his.api.handlers import AuthorizedService

from .errors import NotADirectory, NotAFile, NoSuchNode, WriteError, \
    DeletionError, NoFileNameSpecified, InvalidFileName, NoDataProvided, \
    FileExists, FileCreated, FileUpdated, FileDeleted, FileUnchanged, \
    NotExecutable, NotWritable
from .orm import Inode


__all__ = ['FS']


class FS(AuthorizedService):
    """Service that manages files"""

    NODE = 'fs'
    NAME = 'FileSystem'
    DESCRIPTION = 'Dateisystem'
    PROMOTE = False

    def get(self):
        """Retrieves (a) file(s)"""
        if self.resource is None:
            return JSON(Inode.fsdict(owner=self.account, group=self.customer))
        else:
            inode = Inode.by_path(
                self.resource,
                owner=self.account,
                group=self.customer)

            with suppress(KeyError):
                # Access environ first to provoke KeyError
                # before SHA-256 sum is derived.
                if self.environ['HTTP_IF_NONE_MATCH'] == inode.sha256sum:
                    return FileUnchanged()

            if self.query.get('sha256sum', False):
                return OK(inode.sha256sum)
            else:
                return Binary(inode.data)

    def post(self):
        """Adds new files"""
        if self.resource is None:
            raise NoFileNameSpecified()
        else:
            try:
                Inode.by_path(
                    self.resource,
                    owner=self.account,
                    group=self.customer)
            except NoSuchNode:
                basedir = dirname(self.resource)
                parent = Inode.by_path(
                    basedir,
                    owner=self.account,
                    group=self.customer)

                if parent.isdir:
                    if parent.executable_by(self.account):
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
                                # TODO: Set mode

                                if self.data:
                                    inode.data = self.data

                                inode.save()
                                return FileCreated()
                        else:
                            raise NotWritable() from None
                    else:
                        raise NotExecutable() from None
                else:
                    raise NotADirectory() from None
            else:
                raise FileExists() from None

    def put(self):
        """Overrides an existing file"""
        if self.resource is None:
            raise NoFileNameSpecified()
        else:
            try:
                inode = Inode.by_path(
                    self.resource,
                    owner=self.account,
                    group=self.customer)
            except (NoSuchNode, NotADirectory) as e:
                raise e from None
            else:
                try:
                    name = self.query['name']
                except KeyError:
                    if self.data:
                        try:
                            inode.data = self.data
                        except (NotAFile, WriteError) as e:
                            raise e from None
                        else:
                            inode.save()
                            return FileUpdated()
                    else:
                        raise NoDataProvided()
                else:
                    inode.name = name
                    inode.save()
                    return FileUpdated()

    def delete(self):
        """Deletes a file"""
        try:
            inode = Inode.by_path(
                self.resource,
                owner=self.account,
                group=self.customer)
        except (NoSuchNode, NotADirectory) as e:
            raise e from None
        else:
            try:
                inode.remove(recursive=self.query.get('recursive', False))
            except FileError:
                raise DeletionError() from None
            else:
                return FileDeleted()

    def options(self):
        """Returns options information"""
        return OK()
