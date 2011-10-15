#! /usr/bin/env python

import os
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name = 'ht-deployment',
    version = '0.1.1',
    description = 'Deployment of Hypertable using Fabric',
    long_description = read('README.rst'),
    license = 'Apache License, Version 2.0',
    keywords = 'Hypertable Deployment Fabric',
    author = 'Sreejith K / K7Computing Pvt Ltd',
    author_email = 'sreejithemk@gmail.com',
    url = 'https://github.com/semk/ht-deployment',
    download_url = 'https://github.com/semk/ht-deployment/tarball/master#egg=ht-deployment-0.1.1',
    install_requires = [
        'Fabric >= 1.2.2',
    ],
    setup_requires = [],
    packages = find_packages(exclude=['ez_setup']),
    scripts = ['scripts/ht-deploy'],
    include_package_data = True,
    platforms = ['UNIX'],
    classifiers = [
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
    zip_safe = True
)
