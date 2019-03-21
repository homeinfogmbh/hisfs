"""File utilities."""

from tempfile import TemporaryFile

from mimeutil import mimetype
from wand.image import Image    # pylint: disable=E0401

from hisfs.config import LOGGER


__all__ = ['is_pdf', 'pdfimages']


def is_pdf(blob):
    """Determines whether a file is a PDF document."""

    return mimetype(blob) == 'application/pdf'


def pdfimages(blob, format, resolution=300):    # pylint: disable=W0622
    """Yields pages as images from a PDF file."""

    with Image(blob=blob, resolution=resolution) as pdf:
        for num, page in enumerate(pdf.sequence, start=1):
            LOGGER.info('Converting page #%i.', num)

            with page.clone() as image:
                image.format = format

                with TemporaryFile(mode='w+b') as tmp:
                    image.save(file=tmp)
                    tmp.flush()
                    tmp.seek(0)
                    yield tmp.read()
