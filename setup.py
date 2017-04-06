#! /usr/bin/env python3

from distutils.core import setup


setup(
    name='his.fs',
    version='latest',
    author='Richard Neumann',
    requires=['his'],
    package_dir={'his.mods': ''},
    packages=['his.mods.fs'],
    data_files=[('/etc/his.d/locale', ['files/etc/his.d/locale/fs.ini'])],
    description='HOMEINFO Integrated Services File System')
