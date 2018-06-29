"""File action hooks."""

from logging import INFO, basicConfig, getLogger
from traceback import format_exc

from hisfs.config import LOG_FORMAT, HOOKS

__all__ = ['run_delete_hooks']


LOGGER = getLogger('hisfs.hooks')
basicConfig(level=INFO, format=LOG_FORMAT)


def _load_callable(string):
    """Loads the respective callable."""

    package, *modules, callable_ = string.split('.')

    try:
        package = __import__(package)
    except ImportError:
        LOGGER.error('No such package: %s.', package)
        raise

    for module in modules:
        try:
            package = getattr(package, module)
        except AttributeError:
            LOGGER.error('No module: %s in %s.', module, package)
            raise

    return getattr(package, callable_)


def _run_hooks(hooks, ident):
    """Runs the respective hooks."""

    for hook in hooks:
        LOGGER.info('Running hook: %s().', hook)

        try:
            callable_ = _load_callable(hook)
        except (ImportError, AttributeError):
            continue

        try:
            callable_(ident)
        except Exception as exception:
            LOGGER.error('Failed to run hook: %s\n%s.', hook, exception)
            LOGGER.debug(format_exc())


def run_delete_hooks(ident):
    """Runs the respective deletion hooks."""

    _run_hooks(HOOKS.get('on_delete', ()), ident)
