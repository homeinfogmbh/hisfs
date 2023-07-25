#! /usr/bin/env python3

from setuptools import setup


setup(
    name="hisfs",
    use_scm_version={"local_scheme": "node-and-timestamp"},
    setup_requires=["setuptools_scm"],
    install_requires=[
        "pillow",
        "configlib",
        "filedb",
        "flask",
        "his",
        "mdb",
        "peewee",
        "peeweeplus",
        "wsgilib",
    ],
    author="HOMEINFO - Digitale Informationssysteme GmbH",
    author_email="<info@homeinfo.de>",
    maintainer="Richard Neumann",
    maintainer_email="<r.neumann@homeinfo.de>",
    packages=["hisfs"],
    description="HOMEINFO Integrated Services File System",
)
