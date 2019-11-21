"""File utilities."""

from tempfile import TemporaryFile

from wand.image import Image    # pylint: disable=E0401
from wand.exceptions import CorruptImageError   # pylint: disable=E0611

from hisfs.config import LOGGER
from hisfs.messages import CORRUPT_PDF


__all__ = ['pdfimages']


def _pdfimages(filename, format, resolution=300):    # pylint: disable=W0622
    """Yields pages as images from a PDF file."""

    with Image(filename=filename, resolution=resolution) as pdf:
        for num, page in enumerate(pdf.sequence, start=1):
            LOGGER.info('Converting page #%i.', num)

            with page.clone() as image:
                image.format = format

                with TemporaryFile(mode='w+b') as tmp:
                    image.save(file=tmp)
                    tmp.flush()
                    tmp.seek(0)
                    yield tmp.read()


def pdfimages(file, format, resolution=300):    # pylint: disable=W0622
    """Safely yields PDF images."""

    try:
        yield from _pdfimages(file.path, format, resolution=resolution)
    except CorruptImageError:
        raise CORRUPT_PDF
