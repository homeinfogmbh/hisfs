"""File management module"""

from os.path import dirname, basename
from contextlib import suppress

from homeinfo.crm import Customer
from homeinfo.lib.wsgi import OK, JSON, Binary
from filedb import FileError

from his.api.errors import NotAnInteger
from his.api.handlers import AuthorizedService
from his.orm import Account

from .errors import NotADirectory, NoSuchNode, DeletionError, \
    NoFileNameSpecified, InvalidFileName, FileExists, FileCreated, \
    FileDeleted, FileUnchanged, NotExecutable, NotWritable, NotReadable
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
    def owner(self):
        """Returns the respective owner"""
        try:
            owner = self.query['owner']
        except KeyError:
            return self.account
        else:
            return Account.find(owner)

    @property
    def group(self):
        """Returns the respective group"""
        try:
            group = self.query['group']
        except KeyError:
            return self.customer
        else:
            return Customer.find(group)

    @property
    def recursive(self):
        """Returns the recursive flag"""
        return self.query.get('recursive', False)

    def node_path(self, path):
        """Returns the inode for the respective path"""
        return Inode.node_path(path, owner=self.owner, group=self.group)

    def get(self):
        """Retrieves (a) file(s)"""
        if self.resource is None:
            root = Inode.root_for(owner=self.owner, group=self.group)
            return JSON(root.dict_for(self.account))
        else:
            *parents, inode = self.node_path(self.resource)

            for parent in parents:
                if not parent.executable_by(self.account):
                    raise NotExecutable() from None

            if inode.isdir:
                if inode.executable_by(self.account):
                    if inode.readable_by(self.account):
                        return JSON(inode.to_dict())
                    else:
                        raise NotReadable() from None
                else:
                    raise NotExecutable() from None
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
                self.node_path(self.resource)
            except NoSuchNode:
                *parents, parent = self.node_path(dirname(self.resource))

                for parent_ in parents:
                    if not parent_.executable_by(self.account):
                        raise NotExecutable() from None

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

                                if self.data:
                                    inode.data = self.data

                                inode.mode = self.mode
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

    def delete(self):
        """Deletes a file"""
        try:
            inode = Inode.node_path(
                self.resource,
                owner=self.owner,
                group=self.group)
        except (NoSuchNode, NotADirectory) as e:
            raise e from None
        else:
            try:
                inode.remove_by(self.account, recursive=self.recursive)
            except FileError:
                raise DeletionError() from None
            else:
                return FileDeleted()

    def options(self):
        """Returns options information"""
        return OK()
