"""Errors of the FS"""

from his.api.messages import HISMessage
from his.api.locale import Language

__all__ = [
    'FileSystemError',
    'NotADirectory',
    'NotAFile',
    'NoSuchNode',
    'ParentDirDoesNotExist',
    'ReadError',
    'WriteError',
    'DirectoryNotEmpty',
    'DeletionError',
    'NoFileNameSpecified',
    'InvalidFileName',
    'NoDataProvided',
    'FileExists',
    'FileCreated',
    'FileUpdated',
    'FileDeleted',
    'FileUnchanged',
    'NotExecutable',
    'NotWritable',
    'NotReadable',
    'RootDeletionError']


class FileSystemError(HISMessage):
    """Indicates errors within the file system"""

    pass


class NotADirectory(FileSystemError):
    """Indicates that an inode is not a
    directory but was expected to be one
    """

    STATUS = 406
    LOCALE = {
        Language.DE_DE: 'Ist kein Ordner.',
        Language.EN_US: 'Not a directory.'}


class NotAFile(FileSystemError):
    """Indicates that an inode is not a
    file but was expected to be one
    """

    STATUS = 406
    LOCALE = {
        Language.DE_DE: 'Ist keine Datei.',
        Language.EN_US: 'Not a file.'}


class NoSuchNode(FileSystemError):
    """Indicates that the respective path node does not exist"""

    STATUS = 404
    LOCALE = {
        Language.DE_DE: 'Knoten nicht vorhanden.',
        Language.EN_US: 'Not such node.'}


class ParentDirDoesNotExist(FileSystemError):
    """Indicates that the requested node's parent does not exist"""

    STATUS = 404
    LOCALE = {
        Language.DE_DE: 'Elternordner nicht vorhanden.',
        Language.EN_US: 'Parent directory does not exist.'}


class ReadError(FileSystemError):
    """Indicates that no data could be read from filedb"""

    STATUS = 500
    LOCALE = {
        Language.DE_DE: 'Lesefehler.',
        Language.EN_US: 'Read error.'}


class WriteError(FileSystemError):
    """Indicates that no data could be written to filedb"""

    STATUS = 500
    LOCALE = {
        Language.DE_DE: 'Schreibfehler.',
        Language.EN_US: 'Write error.'}


class DirectoryNotEmpty(FileSystemError):
    """Indicates that the directory could
    not be deleted because it is not empty
    """

    STATUS = 400
    LOCALE = {
        Language.DE_DE: 'Ordner ist nicht leer.',
        Language.EN_US: 'Directory is not empty.'}


class DeletionError(FileSystemError):
    """Indicates that an inode could not be deleted"""

    STATUS = 500
    LOCALE = {
        Language.DE_DE: 'Fehler beim Löschen.',
        Language.EN_US: 'Deletion error.'}


class NoFileNameSpecified(HISMessage):
    """Indicates that no file name was provided"""

    STATUS = 400
    LOCALE = {
        Language.DE_DE: 'Kein Dateiname angegeben.',
        Language.EN_US: 'No file name specified.'}


class InvalidFileName(HISMessage):
    """Indicates that the given file name is invalid"""

    STATUS = 400
    LOCALE = {
        Language.DE_DE: 'Ungültiger Dateiname.',
        Language.EN_US: 'Invalid file name.'}


class NoDataProvided(HISMessage):
    """Indicates that no data has been provided"""

    STATUS = 400
    LOCALE = {
        Language.DE_DE: 'Keine Daten übergeben.',
        Language.EN_US: 'No data provided.'}


class FileExists(HISMessage):
    """Indicates that the file already exists"""

    STATUS = 409
    LOCALE = {
        Language.DE_DE: 'Datei existiert bereits.',
        Language.EN_US: 'File already exists.'}


class FileCreated(HISMessage):
    """Indicates that the file was successfully created"""

    STATUS = 201
    LOCALE = {
        Language.DE_DE: 'Datei gespeichert.',
        Language.EN_US: 'File created.'}


class FileUpdated(HISMessage):
    """Indicates that the file was successfully updated"""

    STATUS = 200
    LOCALE = {
        Language.DE_DE: 'Datei aktualisiert.',
        Language.EN_US: 'File updated.'}


class FileDeleted(HISMessage):
    """Indicates that the file was successfully deleted"""

    STATUS = 200
    LOCALE = {
        Language.DE_DE: 'Datei gelöscht.',
        Language.EN_US: 'File deleted.'}


class FileUnchanged(HISMessage):
    """Indicates that the file was not changed"""

    STATUS = 200
    LOCALE = {
        Language.DE_DE: 'Datei unverändert.',
        Language.EN_US: 'File unchanged.'}


class NotExecutable(HISMessage):
    """Indicates that the inode is not executable"""

    STATUS = 403
    LOCALE = {
        Language.DE_DE: 'Ausführung verweigert.',
        Language.EN_US: 'Execution denied.'}


class NotWritable(HISMessage):
    """Indicates that the inode is not writable"""

    STATUS = 403
    LOCALE = {
        Language.DE_DE: 'Schreiben verweigert.',
        Language.EN_US: 'Writing denied.'}


class NotReadable(HISMessage):
    """Indicates that the inode is not writable"""

    STATUS = 403
    LOCALE = {
        Language.DE_DE: 'Lesen verweigert.',
        Language.EN_US: 'Reading denied.'}


class RootDeletionError(HISMessage):
    """Indicates that the root inode was attempted to be deleted"""

    STATUS = 403
    LOCALE = {
        Language.DE_DE: 'Wurzelverzeichnis darf nicht gelöscht werden.',
        Language.EN_US: 'Deletion of root directory is not permitted.'}
