"""Errors of the FS"""

from his.api.errors import HISMessage
from his.api.locale import Language

__all__ = [
    'FileSystemError',
    'NotADirectory',
    'NotAFile',
    'NoSuchNode',
    'ReadError',
    'WriteError',
    'DirectoryNotEmpty',
    'NoFileNameSpecified',
    'InvalidFileName',
    'NoDataProvided',
    'FileExists',
    'FileCreated',
    'FileUpdated',
    'FileDeleted',
    'FileUnchanged']


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

    def __init__(self, path, *args, **kwargs):
        self.path = path
        super().__init__(*args, **kwargs)


class NotAFile(FileSystemError):
    """Indicates that an inode is not a
    file but was expected to be one
    """

    STATUS = 406
    LOCALE = {
        Language.DE_DE: 'Ist keine Datei.',
        Language.EN_US: 'Not a file.'}

    def __init__(self, path, *args, **kwargs):
        self.path = path
        super().__init__(*args, **kwargs)


class NoSuchNode(FileSystemError):
    """Indicates that the respective path node does not exists"""

    STATUS = 404
    LOCALE = {
        Language.DE_DE: 'Knoten nicht vorhanden.',
        Language.EN_US: 'Not such node.'}

    def __init__(self, path, *args, **kwargs):
        self.path = path
        super().__init__(*args, **kwargs)


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
