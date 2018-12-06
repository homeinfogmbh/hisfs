"""Thumbnail generaor."""

from io import BytesIO
from tempfile import NamedTemporaryFile

from PIL import Image

from hisfs.exceptions import NoThumbnailRequired


__all__ = ['gen_thumbnail']


def gen_thumbnail(bytes_, resolution):
    """Generates a thumbnail for the respective image."""

    bytes_io = BytesIO(bytes_)
    max_x, max_y = resolution
    image = Image.open(bytes_io)
    current_x, current_y = image.size
    fac_x = max_x / current_x
    fac_y = max_y / current_y

    if fac_x >= 1 or fac_y >= 1:
        raise NoThumbnailRequired()

    factor = min(fac_x, fac_y)
    new_x = min(max_x, round(current_x * factor))
    new_y = min(max_y, round(current_y * factor))
    thumbnail_size = (new_x, new_y)
    image.thumbnail(thumbnail_size, Image.ANTIALIAS)

    with NamedTemporaryFile('w+b', suffix='.jpg') as thumbnail:
        image.save(thumbnail, 'JPEG')
        thumbnail.flush()
        thumbnail.seek(0)
        bytes_ = thumbnail.read()

    return (bytes_, thumbnail_size)
