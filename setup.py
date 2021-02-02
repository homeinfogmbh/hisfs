#! /usr/bin/env python3

from setuptools import setup


setup(
    name='hisfs',
    version_format='{tag}',
    setup_requires=['setuptools-git-version'],
    install_requires=[
        'pillow',
        'configlib',
        'filedb',
        'flask',
        'his',
        'mdb',
        'peewee',
        'peeweeplus',
        'wsgilib',
    ],
    author='HOMEINFO - Digitale Informationssysteme GmbH',
    author_email='<info@homeinfo.de>',
    maintainer='Richard Neumann',
    maintainer_email='<r.neumann@homeinfo.de>',
    packages=['hisfs'],
    description='HOMEINFO Integrated Services File System'
)
