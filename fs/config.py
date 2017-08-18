"""File system configuration file parsing"""

from configparserplus import ConfigParserPlus

__all__ = ['config']

config = ConfigParserPlus('/etc/his.d/fs.conf')
