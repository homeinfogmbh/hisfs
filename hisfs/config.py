"""Configuration parser."""

from logging import getLogger

from configlib import load_ini, load_json


__all__ = ['CONFIG', 'DEFAULT_QUOTA', 'LOG_FORMAT', 'LOGGER']


CONFIG = load_ini('hisfs.conf')
DEFAULT_QUOTA = int(CONFIG['fs']['quota'])
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
LOGGER = getLogger('hisfs')
