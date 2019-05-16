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

import multiprocessing
from pyrunner.core.node import ExecutionNode

@pytest.fixture
def node(module=None, worker=None):
  '''Returns a root ExecutionNode with 1 id'''
  manager = multiprocessing.Manager()
  node = ExecutionNode(1)
  node.name = 'Test'
  node.worker_dir = '{}/python'.format(os.path.dirname(os.path.realpath(__file__)))
  node.context = manager.dict()
  if module and worker:
    node.module = module
    node.worker = worker
  return node

@pytest.mark.parametrize('module, worker, exp_retcode', [
  ('sample', 'SayHello', 0),
  ('sample', 'FailMe', 1)
])
def test_return_code(node, module, worker, exp_retcode):
  node.module = module
  node.worker = worker
  node.execute()
  rc = node.poll(True)
  assert rc == exp_retcode

@pytest.mark.parametrize('module, worker', [
  ('exceptions', 'ThrowValueError'),
  ('exceptions', 'ThrowRuntimeError'),
  ('exceptions', 'InvalidInt')
])
def test_exception_returns_nonzero(node, module, worker):
  node.module = module
  node.worker = worker
  node.execute()
  rc = node.poll(True)
  assert rc > 0

invalid_str_list = ['', None, ' ']

@pytest.mark.parametrize('invalid_string', invalid_str_list)
def test_raise_value_error_set_name(node, invalid_string):
  with pytest.raises(ValueError):
    node.name = invalid_string

@pytest.mark.parametrize('invalid_string', invalid_str_list)
def test_raise_value_error_set_worker_dir(node, invalid_string):
  with pytest.raises(ValueError):
    node.worker_dir = invalid_string

@pytest.mark.parametrize('invalid_string', invalid_str_list)
def test_raise_value_error_set_worker(node, invalid_string):
  with pytest.raises(ValueError):
    node.worker = invalid_string

@pytest.mark.parametrize('invalid_string', invalid_str_list)
def test_raise_value_error_set_module(node, invalid_string):
  with pytest.raises(ValueError):
    node.module = invalid_string

@pytest.mark.parametrize('invalid_val', [-2, -99, '-9', '', 'asdf'])
def test_raise_value_error_set_id(node, invalid_val):
  with pytest.raises(ValueError):
    node.id = invalid_val

@pytest.mark.parametrize('invalid_val', [None, {'wat': 'is this'}])
def test_raise_type_error_set_id(node, invalid_val):
  with pytest.raises(TypeError):
    node.id = invalid_val

@pytest.mark.parametrize('invalid_val', [-3, -99, '-9', '', 'asdf'])
def test_raise_value_error_set_retcode(node, invalid_val):
  with pytest.raises(ValueError):
    node.retcode = invalid_val

@pytest.mark.parametrize('invalid_val', [None, {'wat': 'is this'}])
def test_raise_type_error_set_retcode(node, invalid_val):
  with pytest.raises(TypeError):
    node.retcode = invalid_val

@pytest.mark.parametrize('invalid_val', [0, -99, '-9', '', 'asdf'])
def test_raise_value_error_set_max_attempts(node, invalid_val):
  with pytest.raises(ValueError):
    node.max_attempts = invalid_val

@pytest.mark.parametrize('invalid_val', [None, {'wat': 'is this'}])
def test_raise_type_error_set_max_attempts(node, invalid_val):
  with pytest.raises(TypeError):
    node.max_attempts = invalid_val

@pytest.mark.parametrize('invalid_val', [-1, -99, '-9', '', 'asdf'])
def test_raise_value_error_set_retry_wait_time(node, invalid_val):
  with pytest.raises(ValueError):
    node.retry_wait_time = invalid_val

@pytest.mark.parametrize('invalid_val', [None, {'wat': 'is this'}])
def test_raise_type_error_set_retry_wait_time(node, invalid_val):
  with pytest.raises(TypeError):
    node.retry_wait_time = invalid_val