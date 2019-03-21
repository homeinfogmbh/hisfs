"""File utilities."""

from tempfile import TemporaryFile

from mimeutil import mimetype
from wand.image import Image    # pylint: disable=E0401

__all__ = ['is_pdf', 'pdfimages']


def is_pdf(blob):
    """Determines whether a file is a PDF document."""

    return mimetype(blob) == 'application/pdf'


def pdfimages(blob, format, resolution=300):    # pylint: disable=W0622
    """Yields pages as images from a PDF file."""

    with Image(blob=blob, resolution=resolution) as pdf:
        for page in pdf.sequence:
            with page.clone() as image:
                with TemporaryFile(mode='w+b') as tmp:
                    print('DEBUG:' type(image), image, flush=True)
                    print('DEBUG:' dir(image), flush=True)
                    image.save(tmp, format)
                    tmp.flush()
                    tmp.seek(0)
                    yield tmp.read()
