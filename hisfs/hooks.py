"""File action hooks."""

from importlib import import_module
from logging import INFO, basicConfig, getLogger
from traceback import format_exc
from typing import NamedTuple

from hisfs.config import LOG_FORMAT, HOOKS


__all__ = ['run_delete_hooks']


LOGGER = getLogger('hisfs.hooks')
basicConfig(level=INFO, format=LOG_FORMAT)


class LoadingError(Exception):
    """Indicates an error while loading the respective callable."""


def run_delete_hooks(ident):
    """Runs the respective deletion hooks."""

    for hook in Hook.load('on_delete'):
        hook(ident)


class Hook(NamedTuple):
    """Represents a hook."""

    name: str
    package: str
    module: str
    function: str

    def __call__(self, ident):
        """Runs the hook."""
        LOGGER.info('Running hook: %s.', self)

        try:
            self.callable(ident)    # pylint: disable=E1102
        except LoadingError as loading_error:
            LOGGER.error(loading_error)
        except Exception as exception:  # pylint: disable=W0703
            LOGGER.error('Failed to run hook: %s\n%s.', self, exception)
            LOGGER.debug(format_exc())

    @classmethod
    def from_dict(cls, dictionary):
        """Loads the hook from the given dictionary."""
        return cls(
            dictionary.get('name'), dictionary.get('package'),
            dictionary.get('module'), dictionary.get('function'))

    @classmethod
    def load(cls, event):
        """Yields all hooks for the respective event."""
        for hook in HOOKS.get(event) or ():
            yield Hook.from_dict(hook)

    @property
    def callable(self):
        """Loads the hook callable."""
        try:
            module = import_module(f'{self.module}.{self.function}')
        except ImportError:
            raise LoadingError('No such module: %s.' % module)

        try:
            return getattr(module, self.function)
        except AttributeError:
            raise LoadingError('No member %s in %s.' % (self.function, module))
