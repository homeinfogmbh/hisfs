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
    description='HOMEINFO Integrated Services File System')


from his.mods.fs.orm import Inode
from his.mods.fs.wsgi import FS

Inode.create_table(fail_silently=True)
FS.install()
