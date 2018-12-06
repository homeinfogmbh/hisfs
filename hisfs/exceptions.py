"""Common exceptions."""


__all__ = ['UnsupportedFileType', 'NoThumbnailRequired']


class UnsupportedFileType(Exception):
    """Indicates that the respective file is not an image."""

    pass    # pylint: disable=W0107


class NoThumbnailRequired(Exception):
    """Indicates that the original image is of equal
    size or smaller than the requested thumbnail.
    """

    pass    # pylint: disable=W0107
