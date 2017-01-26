"""File system manager"""

from peewee import DoesNotExist
from .orm import INode as ORMInode

__all__ = [
    'FileNotFound',
    'ConsistencyError',
    'INode']


class FileNotFound(Exception):
    """Indicates that the respective file was not found"""

    def __init__(self, path):
        super().__init__(path)
        self.path = path


class ConsistencyError(Exception):
    """Indicates that the consistency of
    the file system has been compromised
    """

    def __init__(self, inode):
        super().__init__(inode)
        self.inode = inode


class INode():
    """Virtual file system"""

    def __init__(self, inode):
        """Sets the targeted orm.INode"""
        self.inode = inode

    @classmethod
    def from_path(cls, path, customer):
        """Returns the INode handler from the respective path"""
        parent = ORMInode.root_for(group=customer)
        processed_path = ['']

        for inode in path.split(ORMInode.PATHSEP):
            if not inode:
                continue
            else:
                processed_path.append(inode)

                try:
                    parent = ORMInode.get(
                        (ORMInode.group == customer) &
                        (ORMInode.parent == parent) &
                        (ORMInode.name == inode))
                except DoesNotExist:
                    raise FileNotFound(ORMInode.PATHSEP.join(processed_path))
        return parent

    def parents_readable(self, account):
        """Determines whether the parents of the INode are readable"""
        parent = self.inode.parent

        while parent is not None:
            if parent.isdir:
                if not parent.executable_by(account):
                    return False
            else:
                raise ConsistencyError(parent)

        return True

    def readable_by(self, account):
        """Determines whether the account can read the targeted INode"""
        return (self.inode.readable_by(account) and
                self.parents_readable(account))

    def writable_by(self, account):
        """Determines whether the account can write the targeted INode"""
        return (self.inode.writable_by(account) and
                self.parents_readable(account))

    def executable_by(self, account):
        """Determines whether the account can execute the targeted INode"""
        return (self.inode.executable_by(account) and
                self.parents_readable(account))
