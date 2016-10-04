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
    packages=['fs'],
    data_files=[
        ('/etc', ['files/etc/his.conf']),
        ('/etc/uwsgi/apps-available',
         ['files/etc/uwsgi/apps-available/his.ini']),
        ('/usr/share/his',
         ['files/usr/share/his/his.wsgi'])],
    description='HOMEINFO Integrated Services File System')


from his.orm import tables

for table in tables:
    table.create_table(fail_silently=True)


from his.mods.meta import install

for handler in install:
    handler.install()
