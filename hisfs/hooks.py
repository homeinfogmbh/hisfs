"""File action hooks."""

from logging import INFO, basicConfig, getLogger
from traceback import format_exc

from hisfs.config import LOG_FORMAT, HOOKS

__all__ = ['run_delete_hooks']


LOGGER = getLogger('hisfs.hooks')
basicConfig(level=INFO, format=LOG_FORMAT)


def _load_function(string):
    """Loads the respective function."""

    module_path, callable_name = string.rsplit('.', maxsplit=1)

    try:
        module = __import__(module_path)
    except ImportError:
        LOGGER.error('No such module: %s.', module_path)
        raise

    try:
        return getattr(module, callable_name)
    except AttributeError:
        LOGGER.error('No such callable: %s.', callable_name)
        raise


def _run_hooks(hooks, ident):
    """Runs the respective hooks."""

    for hook in hooks:
        try:
            function = _load_function(hook)
        except (ImportError, AttributeError):
            continue

        try:
            function(ident)
        except Exception as exception:
            LOGGER.error('Failed to run hook: %s\n%s.', hook, exception)
            LOGGER.debug(format_exc())


def run_delete_hooks(ident):
    """Runs the respective deletion hooks."""

    _run_hooks(HOOKS.get('on_delete', ()), ident)
