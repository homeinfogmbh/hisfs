"""File IO."""

from tempfile import TemporaryFile


__all__ = ['FileContext']


READ = 'rb'
WRITE = 'wb'
MODES = {READ, WRITE}


class FileContext:
    """Acts like a file."""

    def __init__(self, mode, file, *, chunk_size=4096):
        """Sets the file ORM model."""
        if mode not in MODES:
            raise ValueError('Mode must be one of: %s.' % MODES)

        self.mode = mode
        self.file = file
        self.chunk_size = chunk_size
        self.tempfile_context = None
        self.tempfile = None

    def __enter__(self):
        """Opens a tempfile."""
        self.tempfile_context = TemporaryFile(mode='w+b')
        self.tempfile = self.tempfile_context.__enter__()

        if self.mode == READ:
            for chunk in self.file.stream(chunk_size=self.chunk_size):
                self.tempfile.write(chunk)

            self.tempfile.flush()
            self.tempfile.seek(0)

        return self.tempfile

    def __exit__(self, typ, value, traceback):
        """Closes the tempfile."""
        if self.mode == WRITE:
            self.tempfile.flush()
            self.tempfile.seek(0)
            self.file.bytes = self.tempfile.read()  # TODO: Also stream here.

        self.tempfile = None
        tempfile, self.tempfile_context = self.tempfile_context, None
        return tempfile.__exit__(typ, value, traceback)
