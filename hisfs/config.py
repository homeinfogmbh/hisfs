"""Configuration parser."""

from functools import cache, partial
from logging import getLogger

from configlib import load_config


__all__ = ['get_config', 'LOG_FORMAT', 'LOGGER']


get_config = partial(cache(load_config), 'hisfs.conf')
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
LOGGER = getLogger('hisfs')
