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

import pytest
from pyrunner.core.register import NodeRegister
from pyrunner.serde.list import ListSerDe

@pytest.fixture
def register():
  register = NodeRegister(ListSerDe())
  register.add_node(name='Say Hello 1', logfile=None, module='sample', worker='SayHello')
  register.add_node(name='Say Hello 2', logfile=None, module='sample', worker='SayHello')
  register.add_node(name='Say Hello 3', logfile=None, module='sample', worker='SayHello', dependencies=['Say Hello 1'])
  register.add_node(name='Say Hello 4', logfile=None, module='sample', worker='SayHello', dependencies=['Say Hello 1'])
  register.add_node(name='Say Hello 5', logfile=None, module='sample', worker='SayHello', dependencies=['Say Hello 3', 'Say Hello 4'])
  register.add_node(name='Say Hello 6', logfile=None, module='sample', worker='SayHello', dependencies=['Say Hello 5'])
  return register

def test_register_add(register):
  assert len(register.pending_nodes) == 6 and len(register.all_nodes) == 6

def test_register_set_children_defaulted_1(register):
  register.set_children_defaulted(register.find_node(name='Say Hello 1'))
  assert len(register.defaulted_nodes) == 4 and len(register.pending_nodes) == 2 and len(register.all_nodes) == 6

def test_register_set_children_defaulted_2(register):
  register.set_children_defaulted(register.find_node(name='Say Hello 4'))
  assert len(register.defaulted_nodes) == 2 and len(register.pending_nodes) == 4 and len(register.all_nodes) == 6

def test_register_set_all_norun(register):
  register.set_all_norun()
  assert len(register.norun_nodes) == 6 and len(register.all_nodes) == 6

@pytest.mark.parametrize('exec_list, expected', [
  ([1,2,3], [1,2,3]),
  ([], []),
  ([-1,-3,0,1], [1]),
  ([99, 100, 101], [])
])
def test_register_exec_only(register, exec_list, expected):
  register.exec_only(exec_list)
  assert set([ n.id for n in register.pending_nodes ]) == set(expected) and len(register.all_nodes) == 6

@pytest.mark.parametrize('exec_id, expected', [
  (3, [1,3]),
  (-1, []),
  (0, []),
  (1, [1]),
  (100, []),
  (6, [1,3,4,5,6])
])
def test_register_exec_to(register, exec_id, expected):
  register.exec_to(exec_id)
  assert set([ n.id for n in register.pending_nodes ]) == set(expected) and len(register.all_nodes) == 6

@pytest.mark.parametrize('exec_id, expected', [
  (3, [3,5,6]),
  (-1, [1,2,3,4,5,6]),
  (0, []),
  (1, [1,3,4,5,6]),
  (100, []),
  (6, [6])
])
def test_register_exec_from(register, exec_id, expected):
  register.exec_from(exec_id)
  assert set([ n.id for n in register.pending_nodes ]) == set(expected) and len(register.all_nodes) == 6

@pytest.mark.parametrize('exec_list, expected', [
  ([1,2,3], [4,5,6]),
  ([], [1,2,3,4,5,6]),
  ([-1,-3,0,1], [2,3,4,5,6]),
  ([99, 100, 101], [1,2,3,4,5,6]),
  ([1,2,3,4,5,6], [])
])
def test_register_exec_disable(register, exec_list, expected):
  register.exec_disable(exec_list)
  assert set([ n.id for n in register.pending_nodes ]) == set(expected) and len(register.all_nodes) == 6