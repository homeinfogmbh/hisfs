"""File management module"""

from os.path import dirname, basename
from hashlib import sha256

from homeinfo.lib.mime import mimetype
from homeinfo.lib.wsgi import OK, JSON

from his.api.handlers import AuthorizedService

from .errors import NotADirectory, NotAFile, NoSuchNode, ReadError, \
    WriteError, DirectoryNotEmpty, NoFileNameSpecified, InvalidFileName, \
    NoDataProvided, FileExists, FileCreated, FileUpdated, FileDeleted
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
            try:
                inode = Inode.by_path(
                    self.resource,
                    owner=self.account,
                    group=self.customer)
            except (NoSuchNode, NotADirectory) as e:
                raise e from None
            else:
                try:
                    data = inode.data
                except (NotAFile, ReadError) as e:
                    raise e from None
                else:
                    if self.query_dict.get('sha256sum', False):
                        return OK(sha256(data).hexdigest())
                    else:
                        return OK(data, content_type=mimetype(data),
                                  charset=None)

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
                try:
                    parent = Inode.by_path(
                        dirname(self.resource),
                        owner=self.account,
                        group=self.customer)
                except (NoSuchNode, NotADirectory) as e:
                    raise e from None
                else:
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
                            # File
                            inode.file = inode.client.add(self.data)
                        else:
                            # Directory
                            inode.file = None

                        inode.save()
                        return FileCreated()
            except NotADirectory as e:
                raise e from None
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
                    name = self.query_dict['name']
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
                inode.remove(recursive=self.query_dict.get('recursive', False))
            except DirectoryNotEmpty as e:
                raise e from None
            else:
                return FileDeleted()
