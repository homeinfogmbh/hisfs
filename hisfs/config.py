"""Configuration parser."""

from configlib import load_ini, load_json


__all__ = ['LOG_FORMAT', 'CONFIG', 'DEFAULT_QUOTA', 'HOOKS']


LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
CONFIG = load_ini('hisfs.conf')
DEFAULT_QUOTA = int(CONFIG['fs']['quota'])
HOOKS = load_json('hisfs.hooks')
