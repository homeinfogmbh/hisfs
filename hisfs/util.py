"""File utilities."""

from tempfile import NamedTemporaryFile

from mimeutil import mimetype
from wand.image import Image

__all__ = ['is_pdf', 'pdfimages']


def is_pdf(blob):
    """Determines whether a file is a PDF document."""

    return mimetype(blob) == 'application/pdf'


def pdfimages(blob, suffix='.jpeg', resolution=300):
    """Yields pages as images from a PDF file."""

    with Image(blob=blob, resolution=resolution) as pdf:
        for page in pdf.sequence:
            with page.clone() as image:
                with NamedTemporaryFile(mode='w+b', suffix=suffix) as tmp:
                    # Does not work with file keyword argument.
                    image.save(filename=tmp.name)
                    tmp.flush()
                    tmp.seek(0)
                    yield tmp.read()
