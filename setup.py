#!/usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2019 Jean-Fabrice
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from setuptools import setup, find_packages
import os

__author__ = "Jean-Fabrice"
__license__ ="MIT"
__modulename__ = "vmware2dhcp"
__revision__ = ''
__email__ = "github@bobo-rousselin.com"
__url__ = "https://github.com/jeanfabrice/vmware2dhcp"
__description__ = "Populate isc-dhcp-server with VMs living in a VMware environment"

with open(os.path.join(__modulename__, 'VERSION'), "r") as fh:
  __version__ = fh.readline().strip()

with open("README.md", "r") as fh:
  long_description = fh.read()

if __name__ == '__main__':
  setup(
    name = __modulename__,
    version = __version__,
    author = __author__,
    author_email = __email__,
    classifiers = [
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Development Status :: 4 - Beta',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
    ],
    description = __description__,
    entry_points = {
      'console_scripts': [
          'vmware2dhcp-cli = vmware2dhcp.cli:run'
      ],
    },
    install_requires = [
      'pypureomapi~=0.6',
      'pytz~=2018.9',
      'pyvmomi~=6.7',
      'PyYAML~=5.1',
      'prometheus-client~=0.6'
    ],
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = __url__,
    packages = find_packages(),
    python_requires = '>=3',
    include_package_data=True
)
