"""Thumbnail generaor."""

from io import BytesIO
from mimetypes import guess_extension
from tempfile import NamedTemporaryFile

from PIL import Image

from hisfs.exceptions import NoThumbnailRequired


__all__ = ['gen_thumbnail']


def _get_new_resolution(original_resolution, desired_resolution):
    """Returns a new ewsolution with kept aspect ratio."""

    current_x, current_y = original_resolution
    max_x, max_y = desired_resolution
    fac_x = max_x / current_x
    fac_y = max_y / current_y

    if fac_x >= 1 or fac_y >= 1:
        raise NoThumbnailRequired()

    factor = min(fac_x, fac_y)
    new_x = min(max_x, round(current_x * factor))
    new_y = min(max_y, round(current_y * factor))
    return (new_x, new_y)


def gen_thumbnail(bytes_, resolution, mimetype):
    """Generates a thumbnail for the respective image."""

    bytes_io = BytesIO(bytes_)
    image = Image.open(bytes_io)
    thumbnail_size = _get_new_resolution(image.size, resolution)
    image.thumbnail(thumbnail_size, Image.ANTIALIAS)
    suffix = guess_extension(mimetype) or '.jpeg'
    frmt = suffix[1:].upper()

    with NamedTemporaryFile('w+b', suffix=suffix) as thumbnail:
        image.save(thumbnail, frmt)
        thumbnail.flush()
        thumbnail.seek(0)
        bytes_ = thumbnail.read()

    return (bytes_, thumbnail_size)
