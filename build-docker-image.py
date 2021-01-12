#!/usr/bin/env python
# -*- coding: utf8 -*-
# Copyright (c) 2019 Jean-Fabrice
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from datetime import datetime, timezone
import subprocess
import setup

subprocess.call([
  "docker",
  "build",
  "--build-arg",
  "AUTHOR="+setup.__author__,
  "--build-arg",
  "CREATED="+datetime.now(timezone.utc).astimezone().isoformat('T'),
  "--build-arg",
  "DESCRIPTION="+setup.__description__,
  "--build-arg",
  "EMAIL="+setup.__email__,
  "--build-arg",
  "LICENSES="+setup.__license__,
  "--build-arg",
  "REVISION="+setup.__revision__,
  "--build-arg",
  "SOURCE="+setup.__url__,
  "--build-arg",
  "TITLE="+setup.__modulename__,
  "--build-arg",
  "VERSION="+setup.__version__,
  "-t",
  setup.__modulename__+':'+setup.__version__,
  "."
]
)
