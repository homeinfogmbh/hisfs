"""Configuration parser."""

from configlib import INIParser

__all__ = ['CONFIG']


CONFIG = INIParser('/etc/hisfs.conf')
DEFAULT_QUOTA = int(CONFIG['fs']['quota'])
