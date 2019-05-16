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

import os
import pytest
from pyrunner.serde.list import ListSerDe

@pytest.fixture
def proc_file():
  return '{}/config/tests.lst'.format(os.path.dirname(os.path.realpath(__file__)))

@pytest.fixture
def proc_dict():
  return parser.load_proc_list('{}/config/tests.lst'.format(os.path.dirname(os.path.realpath(__file__))))