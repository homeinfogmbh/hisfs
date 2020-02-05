"""File utilities."""

from tempfile import TemporaryFile

from wand.image import Image    # pylint: disable=E0401
from wand.exceptions import CorruptImageError   # pylint: disable=E0611

from hisfs.config import LOGGER
from hisfs.messages import CORRUPT_PDF


__all__ = ['DEFAULT_DPI', 'pdfimages']


DEFAULT_DPI = 300


# pylint: disable=W0622
def _pdfimages(filename, format, dpi=DEFAULT_DPI):
    """Yields pages as images from a PDF file."""

    with Image(filename=filename, resolution=dpi) as pdf:
        for num, page in enumerate(pdf.sequence, start=1):
            LOGGER.info('Converting page #%i.', num)

            with page.clone() as image:
                image.format = format

                with TemporaryFile(mode='w+b') as tmp:
                    image.save(file=tmp)
                    tmp.flush()
                    tmp.seek(0)
                    yield tmp.read()


# pylint: disable=W0622
def pdfimages(file, format, dpi=DEFAULT_DPI):
    """Safely yields PDF images."""

    try:
        yield from _pdfimages(file.path, format, dpi=dpi)
    except CorruptImageError:
        raise CORRUPT_PDF
