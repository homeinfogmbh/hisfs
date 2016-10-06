"""File management module"""

from os.path import dirname, basename
from hashlib import sha256

from peewee import DoesNotExist

from homeinfo.lib.mime import mimetype

from his.api.locale import Language
from his.api.errors import HISMessage, NotAuthorized
from his.api.handlers import AuthorizedService

from .orm import NotAFile, FileNotFound, Inode


class NoFileNameSpecified(HISMessage):
    """Indicates that the file already exists"""

    STATUS = 400
    LOCALE = {
        Language.DE_DE: 'Kein Dateiname angegeben.',
        Language.EN_US: 'No file name specified.'}


class FileExists(HISMessage):
    """Indicates that the file already exists"""

    STATUS = 400
    LOCALE = {
        Language.DE_DE: 'Datei existiert bereits.',
        Language.EN_US: 'File already exists.'}


class FileManager(AuthorizedService):
    """Service that manages files"""

    @property
    def owner(self):
        """Optional owner argument for root and admins"""
        try:
            owner = self.query_dict['owner']
        except KeyError:
            return None
        else:
            try:
                return Account.find(owner)
            except DoesNotExist:
                return None

    @property
    def group(self):
        """Optional group argument for root"""
        try:
            group = self.query_dict['group']
        except KeyError:
            return None
        else:
            try:
                return Customer.find(group)
            except DoesNotExist:
                return None

    @property
    def verified_owner(self):
        """Gets the verified owner"""
        if self.account.root:
            return self.owner or self.account
        elif self.account.admin:
            try:
                owner = self.owner
            except AttributeError:
                return self.account.customer
            else:
                if owner.customer == self.account.customer:
                    return owner
                else:
                    raise NotAuthorized()
        else:
            return self.account

    @property
    def verified_group(self):
        """Gets the verified group"""
        if self.account.root:
            return self.group or self.account.customer
        else:
            return self.account.customer


    def get(self):
        """Retrieves (a) file(s)"""
        if self.resource is None:
            return JSON(Inode.fsdict(
                owner=self.verified_owner,
                group=self.verified_group)
        else:
            try:
                inode = Inode.by_path(
                    self.resource,
                    owner=self.verified_owner,
                    group=self.verified_group)
            except (NoSuchNode, NotADirectory) as e:
                raise e from None
            else:
                try:
                    data = inode.data
                except (NotAFile, FileNotFound) as e:
                    raise e from None
                else:
                    try:
                        sha256sum = self.query_dict['sha256sum']
                    except KeyError:
                        sha256sum = False

                    if sha256sum:
                        return OK(sha256(data).hexdigest())
                    else:
                        return OK(data, content_type=mimetype(data),
                                  charset=None)

    def post(self):
        """Adds new files"""
        if self.resource is None:
            raise NoFileNameSpecified()
        else:
            owner = self.verified_owner
            group = self.verified_group

            try:
                Inode.by_path(self.resource, owner=owner, group=group)
            except NoSuchNode:
                try:
                    parent = Inode.by_path(
                        dirname(self.resource),
                        owner=owner, group=group)
                except (NoSuchNode, NotADirectory) as e:
                    raise e from None
                else:
                    inode = Inode()

                    try:
                        inode.name = basename(self.resource)
                    except ValueError:
                        raise InvalidFileName()
                    else:
                        inode.owner = owner
                        inode.group = group
                        inode.parent = parent

                        try:
                            data = self.file.read()
                        except AttributeError:
                            # Directory
                            inode.file = None
                        else:
                            # File
                            inode.file = inode.client.add(data)

                        inode.save()
                        return OK()
            except NotADirectory as e:
                raise e from None
            else:
                raise FileExists() from None

    def put(self):
        """Overrides an existing file"""
        if self.resource is None:
            raise NoFileNameSpecified()
        else:
            owner = self.verified_owner
            group = self.verified_group

            try:
                inode = Inode.by_path(self.resource, owner=owner, group=group)
            except (NoSuchNode, NotADirectory) as e:
                raise e from None
            else:
                try:
                    data = self.file.read()
                except AttributeError:
                    raise NoDataProvided() from None
                else:
                    try:
                        inode.data = self.file.read()
                    except (NotAFile, WriteError) as e:
                        raise e from None
                    else:
                        inode.save()
                        return OK()

    def delete(self):
        """Deletes a file"""
        try:
            inode = Inode.by_path(
                self.resource,
                owner=self.verified_owner,
                group=self.verified_group)
        except (NoSuchNode, NotADirectory) as e:
            raise e from None
        else:
            try:
                inode.remove(recursive=self.query_dict.get('recursive', False))
            except DirectoryNotEmpty as e:
                raise e from None
