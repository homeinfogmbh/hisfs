#! /usr/bin/env python3

from distutils.core import setup


setup(
    name='hisfs',
    version='latest',
    author='HOMEINFO - Digitale Informationssysteme GmbH',
    author_email='<info at homeinfo dot de>',
    maintainer='Richard Neumann',
    maintainer_email='<r dot neumann at homeinfo period de>',
    requires=['his'],
    packages=['hisfs'],
    data_files=[('/etc/his.d/locale', ['files/fs.ini'])],
    description='HOMEINFO Integrated Services File System')
