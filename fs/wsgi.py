"""File management module"""

from peewee import DoesNotExist

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


class FileManager(AuthorizedService):
    """Service that manages files"""

    def get(self):
        """Retrieves (a) file(s)"""
        if self.resource is None:
            return JSON(Inode.fsdict(cls, owner=self.account))
        else:
            try:
                inode = Inode.by_path(self.resource, account=self.account)
            except (NoSuchNode, NotADirectory):
                raise FileNotFound() from None
            else:
                try:
                    return inode.data
                except NotAFile:
                    # TODO: handle directory
                    pass
                except FileNotFound:
                    raise FileNotAvailable() from None

    def post(self):
        """Adds new files"""
        # TODO: implement
        pass

    def put(self):
        """Updates an existing file"""
        # TODO: implement
        pass

    def delete(self):
        """Deletes a file"""
        # TODO: implement
        pass
