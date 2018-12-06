"""Common exceptions."""


__all__ = ['FileExists', 'UnsupportedFileType', 'NoThumbnailRequired']


class FileExists(Exception):
    """Indicates that a file with the respective name already exists."""

    def __init__(self, file):
        """Sets the existing file."""
        super().__init__()
        self.file = file


class UnsupportedFileType(Exception):
    """Indicates that the respective file is not an image."""

    pass    # pylint: disable=W0107


class NoThumbnailRequired(Exception):
    """Indicates that the original image is of equal
    size or smaller than the requested thumbnail.
    """

    pass    # pylint: disable=W0107
