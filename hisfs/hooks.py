"""File action hooks."""

from importlib import import_module
from logging import INFO, basicConfig, getLogger
from traceback import format_exc

from hisfs.config import LOG_FORMAT, HOOKS

__all__ = ['run_delete_hooks']


LOGGER = getLogger('hisfs.hooks')
basicConfig(level=INFO, format=LOG_FORMAT)


class LoadingError(Exception):
    """Indicates an error while loading the respective callable."""

    pass


def _load_callable(string):
    """Loads the respective callable."""

    try:
        module, callable_ = string.rsplit('.', maxsplit=1)
    except ValueError:
        raise LoadingError('Invalid python path: %s.' % string)

    try:
        module = import_module(module)
    except ImportError:
        raise LoadingError('No such module: %s.' % module)

    try:
        return getattr(module, callable_)
    except AttributeError:
        raise LoadingError('No callable %s in %s.' % (callable_, module))


def _run_hooks(hooks, ident):
    """Runs the respective hooks."""

    for hook in hooks:
        LOGGER.info('Running hook: %s().', hook)

        try:
            callable_ = _load_callable(hook)
        except LoadingError as loading_error:
            LOGGER.error(loading_error)
            continue

        try:
            callable_(ident)
        except Exception as exception:
            LOGGER.error('Failed to run hook: %s\n%s.', hook, exception)
            LOGGER.debug(format_exc())


def run_delete_hooks(ident):
    """Runs the respective deletion hooks."""

    _run_hooks(HOOKS.get('on_delete', ()), ident)
