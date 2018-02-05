"""Configuration parser."""

from configlib import INIParser

__all__ = ['CONFIG']


CONFIG = INIParser('/etc/hisfs.conf')
