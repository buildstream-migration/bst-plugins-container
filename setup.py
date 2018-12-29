#!/usr/bin/env python3
#
#  Copyright (C) 2018 Codethink Limited
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library. If not, see <http://www.gnu.org/licenses/>.
#
#  Authors:
#        Tristan Maat <jonathan.maw@codethink.co.uk>

import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    print("BuildStream requires setuptools in order to locate plugins. Install "
          "it using your package manager (usually python3-setuptools) or via "
          "pip (pip3 install setuptools).")
    sys.exit(1)

setup(name='BuildStream-plugins-container',
      version="0.1.0",
      description="A collection of BuildStream plugins that are to do with containers.",
      license='LGPL',
      packages=find_packages(exclude=['tests', 'tests.*']),
      include_package_data=True,
      install_requires=[
          'requests',
          'setuptools'
      ],
      package_data={
          'buildstream': [
              'bst_plugins_container/elements/**.yaml'
          ]
      },
      entry_points={
          'buildstream.plugins': [
              'docker = bst_plugins_docker.sources.docker',
          ]
      },
      setup_requires=['pytest-runner', 'setuptools_scm'],
      tests_require=['pep8',
                     'pytest-datafiles',
                     'pytest-env',
                     'pytest-pep8',
                     'pytest-xdist',
                     'pytest >= 3.1.0'],
      zip_safe=False
)  #eof setup()
