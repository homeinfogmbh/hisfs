"""Configuration parser."""

from logging import getLogger

from configlib import loadcfg


__all__ = ['CONFIG', 'LOG_FORMAT', 'LOGGER']


CONFIG = loadcfg('hisfs.conf')
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
LOGGER = getLogger('hisfs')
