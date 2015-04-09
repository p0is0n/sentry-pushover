#!/usr/bin/env python
'''
Sentry-Pushover
=============
A [Sentry](https://www.getsentry.com/) plugin that sends notofications to a [Pushover](https://pushover.net).

License
-------
Copyright 2012 Janez Troha

This file is part of Sentry-Pushover.

Sentry-Pushover is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Sentry-Pushover is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Sentry-Pushover.  If not, see <http://www.gnu.org/licenses/>.
'''
from setuptools import setup, find_packages

install_requires = [
    'requests',
    'sentry',
]

setup(
    name='sentry-pushover',
    version='1.0.9',
    author='Janez Troha',
    author_email='janez.troha@gmail.com',
    url='https://github.com/dz0ny/sentry-pushover',
    description='A Sentry plugin that integrates with pushover',
    long_description=__doc__,
    license='GPL',
    packages=find_packages(exclude=['tests']),
    package_data = {
        'sentry_pushover': ['templates/sentry_pushover/*.txt'],
    },
    install_requires=install_requires,
    entry_points={
        'sentry.apps': [
            'sentry_pushover = sentry_pushover',
        ],
        'sentry.plugins': [
            'pushover = sentry_pushover.models:PushoverNotifications'
        ]
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
    include_package_data=True,
    zip_safe=False,
)
