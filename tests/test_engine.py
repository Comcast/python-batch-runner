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

from pyrunner.core.engine import ExecutionEngine
from pyrunner.core.register import NodeRegister
from pyrunner.serde import ListSerDe

@pytest.fixture
def engine():
  engine = ExecutionEngine()
  engine.register = NodeRegister()
  engine.config['tickrate'] = 0
  engine.config['worker_dir'] = '{}/python'.format(os.path.dirname(os.path.realpath(__file__)))
  return engine

def test_engine_success(engine):
  engine.register.add_node(name='Say Hello 1', logfile=None, module='sample', worker='SayHello')
  engine.register.add_node(name='Say Hello 2', logfile=None, module='sample', worker='SayHello')
  engine.register.add_node(name='Say Hello 3', logfile=None, module='sample', worker='SayHello', dependencies=['Say Hello 1'])
  res = engine.initiate(silent=False)
  assert res == 0

def test_engine_failure(engine):
  engine.register.add_node(name='Say Hello', logfile=None, module='sample', worker='SayHello')
  engine.register.add_node(name='Fail Me 1', logfile=None, module='sample', worker='FailMe', dependencies=['Say Hello'])
  engine.register.add_node(name='Fail Me 2', logfile=None, module='sample', worker='FailMe', dependencies=['Say Hello'])
  engine.register.add_node(name='Fail Me 3', logfile=None, module='sample', worker='FailMe', dependencies=['Fail Me 2'])
  res = engine.initiate(silent=True)
  assert res == 2