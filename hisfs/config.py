"""Configuration parser."""

from configlib import INIParser, JSONParser

__all__ = ['LOG_FORMAT', 'CONFIG', 'DEFAULT_QUOTA', 'HOOKS']


LOG_FORMAT = '[%(levelname)s] %(name)s: %(message)s'
CONFIG = INIParser('/etc/hisfs.conf', alert=True)
DEFAULT_QUOTA = int(CONFIG['fs']['quota'])
HOOKS = JSONParser('/etc/hisfs.hooks', alert=True)
