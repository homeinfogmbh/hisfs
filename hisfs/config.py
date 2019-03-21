"""Configuration parser."""

from logging import INFO, basicConfig, getLogger

from configlib import load_ini, load_json


__all__ = ['CONFIG', 'DEFAULT_QUOTA', 'HOOKS', 'LOGGER']


CONFIG = load_ini('hisfs.conf')
DEFAULT_QUOTA = int(CONFIG['fs']['quota'])
HOOKS = load_json('hisfs.hooks')
LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
LOGGER = getLogger(__file__)
basicConfig(level=INFO, format=LOG_FORMAT)
