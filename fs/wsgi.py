"""File management module"""

from os.path import dirname, basename

from peewee import DoesNotExist

from homeinfo.lib.mime import mimetype

from his.api.locale import Language
from his.api.errors import HISMessage
from his.api.handlers import AuthorizedService

from .orm import NotAFile, FileNotFound, Inode


class FileSystemError(HISMessage):
    """Indicates that the respective file is not available"""

    STATUS = 500
    LOOCALE = {
        Language.DE_DE: 'Dateisystemfehler.',
        Language.EN_US: 'File system error.'}


class FileNotAvailable(FileSystemError):
    """Indicates that the respective file is not available"""

    STATUS = 500
    LOOCALE = {
        Language.DE_DE: 'Datei nicht verfügbar.',
        Language.EN_US: 'File not available.'}


class FileNotFound(FileSystemError):
    """Indicates that the respective file is not available"""

    STATUS = 404
    LOOCALE = {
        Language.DE_DE: 'Datei nicht gefunden.',
        Language.EN_US: 'File not found.'}


class FileExists(FileSystemError):
    """Indicates that the respective file is not available"""

    STATUS = 400
    LOOCALE = {
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

    def get(self):
        """Retrieves (a) file(s)"""
        if self.resource is None:
            if self.account.root:
                return JSON(Inode.fsdict(owner=self.owner, group=self.group))
            elif self.account.admin:
                owner = self.owner

                if owner is not None:
                    if owner.customer != self.account.customer:
                        raise IsufficientPermissions()

                return JSON(Inode.fsdict(
                    owner=owner,
                    group=self.account.customer))
            else:
                return JSON(Inode.fsdict(
                    owner=self.account,
                    group=self.account.customer))
        else:
            if self.account.root:
                try:
                    inode = Inode.by_path(self.resource)
                except (NoSuchNode, NotADirectory) as e:
                    raise FileNotFound(e.path) from None
            elif self.account.admin:
                try:
                    inode = Inode.by_path(
                        self.resource,
                        group=self.account.customer)
                except (NoSuchNode, NotADirectory) as e:
                    raise FileNotFound(e.path) from None
            else:
                try:
                    inode = Inode.by_path(self.resource, owner=self.account)
                except (NoSuchNode, NotADirectory) as e:
                    raise FileNotFound(e.path) from None

            try:
                data = inode.data
            except NotAFile:
                return JSON(inode.todict())
            except FileNotFound:
                raise FileNotAvailable() from None
            else:
                return OK(data, content_type=mimetype(data), charset=None)

    def post(self):
        """Adds new files"""
        if self.resource is None:
            raise NoFileNameSpecified()
        else:
            try:
                Inode.by_path(self.resource, account=self.account)
            except (NoSuchNode, NotADirectory):
                try:
                    parent = Inode.by_path(
                        dirname(self.resource),
                        account=self.account)
                except (NoSuchNode, NotADirectory)as e:
                    raise FileNotFound(e.path) from None
                else:
                    inode = Inode()

                    try:
                        inode.name = basename(self.resource)
                    except ValueError:
                        raise InvalidFileName()
                    else:
                        inode.owner = self.account
                        inode.group = self.account.customer
                        inode.parent = parent

                        try:
                            data = self.file.read()
                        except AttributeError:
                            inode.file = None
                        else:
                            inode.file = inode.client.add(data)

                        inode.save()
            else:
                raise FileExists() from None

    def put(self):
        """Updates an existing file"""
        # TODO: implement
        pass

    def delete(self):
        """Deletes a file"""
        # TODO: implement
        pass
