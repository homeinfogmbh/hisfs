"""File management module"""

from peewee import DoesNotExist

from his.locale import Language
from his.api.errors import HISMessage
from his.api.handlers import AuthorizedService

from .orm import Inode


class FileManager(AuthorizedService):
    """Service that manages files"""

    def get(self):
        """Retrieves information about a file"""
        if self.resource is None:
            # Retrieves all files
            # TODO: implement
            pass
        else:
            try:
                file_id = int(self.resource)
            except ValueError:
                try:
                    inode = Inode.by_path(self.resource, account=self.account)
                except (NoSuchNode, NotADirectory):
                    raise
                else:
                    try:
                        return inode.data
                    except NotAFile:
                        # TODO: handle
                        pass
                    except FileNotFound:
                        # TODO: handle
                        pass
            else:
                try:
                    inode = Inode.by_id(self.account, file_id)
                except DoesNotExist:
                    # TODO: implement
                    raise NoSuchInode()
                else:
                    try:
                        return inode.data
                    except NotAFile:
                        # TODO: handle
                        pass
                    except FileNotFound:
                        # TODO: handle
                        pass
