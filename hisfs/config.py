"""Configuration parser."""

from configlib import loadcfg, JSONParser

__all__ = ['LOG_FORMAT', 'CONFIG', 'DEFAULT_QUOTA', 'HOOKS']


LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
CONFIG = loadcfg('hisfs.conf')
DEFAULT_QUOTA = int(CONFIG['fs']['quota'])
HOOKS = JSONParser('/usr/local/etc/hisfs.hooks', alert=True)
