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
    scripts=['files/hisfsd'],
    data_files=[
        ('/usr/lib/systemd/system', ['files/hisfs.service']),
        ('/etc/his.d/locale', ['files/fs.ini'])],
    description='HOMEINFO Integrated Services File System')
