#!/usr/bin/python3

# Copyright 2019 Comcast Cable Communications Management, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

import sys
from distutils.core import setup
from pyrunner.version import __version__

setup(
  name = 'python-batch-runner',
  version = __version__,
  author = 'Nathaniel Lee',
  author_email = 'nathaniel_lee@comcast.com',
  install_requires = [],
  packages = ['pyrunner', 'pyrunner.core', 'pyrunner.logger', 'pyrunner.notification', 'pyrunner.serde', 'pyrunner.worker', 'pyrunner.autodoc' ],
  license = 'Apache 2.0',
  long_description = 'Python utility providing text-based workflow manager.',
  entry_points = {
    'console_scripts': ['pyrunner=pyrunner.cli:main']
  }
)