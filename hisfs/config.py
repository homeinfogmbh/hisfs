"""Configuration parser."""

from logging import getLogger

from configlib import load_ini, load_json


__all__ = ['CONFIG', 'DEFAULT_QUOTA', 'HOOKS', 'LOG_FORMAT', 'LOGGER']


CONFIG = load_ini('hisfs.conf')
DEFAULT_QUOTA = int(CONFIG['fs']['quota'])
HOOKS = load_json('hisfs.hooks')
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
LOGGER = getLogger('hisfs')
