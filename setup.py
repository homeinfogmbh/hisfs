#! /usr/bin/env python3

from distutils.core import setup
from homeinfo.lib.misc import GitInfo

version, author, author_email, *_ = GitInfo()

setup(
    name='his.fs',
    version=version,
    author=author,
    author_email=author_email,
    requires=['his'],
    package_dir={'his.mods': ''},
    packages=['his.mods.fs'],
    data_files=[('/etc/his.d/locale', ['files/etc/his.d/locale/fs.ini']),
    description='HOMEINFO Integrated Services File System')
