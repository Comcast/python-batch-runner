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
import os

from pyrunner.core.context import Context
from multiprocessing import Manager
from datetime import datetime

abs_dir_path = os.path.dirname(os.path.realpath(__file__))

@pytest.fixture
def ctx():
  '''Returns an empty Context object with loaded profile'''
  manager = Manager()
  return Context(manager.dict(), manager.Queue())

@pytest.mark.parametrize('key, value', [
  ('A', 1),
  ('TABLENAME', 'employee'),
  ('NONE_VALUE', None),
  ('Nothing', ''),
  ('Some Boolean', True)
])
def test_basic_set_get(ctx, key, value):
  ctx.set(key, value)
  assert value == ctx.get(key)

def test_set_overwrite(ctx):
  ctx.set('MYVAR', 'asdf')
  ctx.set('MYVAR', 'my new value')
  assert ctx.get('MYVAR') == 'my new value'

def test_get_invalid_key_returns_none(ctx):
  assert ctx.get('NOT_REAL') == None

def test_get_invalid_key_return_default_val(ctx):
  assert ctx.get('NOT_REAL', 'my fallback') == 'my fallback'

def test_set_and_modify_object(ctx):
  mydict = { 'a': 1, 'b': 'something' }
  ctx.set('shared_dict', mydict)
  mydict['a'] = 2
  mydict['b'] = 'changed'
  assert ctx.get('shared_dict') != { 'a': 2, 'b': 'changed' }

def test_emulate_setitem(ctx):
  ctx['myvar'] = 1234
  assert ctx.get('myvar') == 1234

def test_emulate_getitem(ctx):
  ctx['myvar'] = 1234
  assert ctx['myvar'] == 1234

def test_emulate_getitem_keyerror(ctx):
  with pytest.raises(KeyError):
    ctx['myvar']

def test_emulate_delitem(ctx):
  ctx['myvar'] = 1234
  del ctx['myvar']
  assert 'myvar' not in ctx

def test_emulate_delitem_keyerror(ctx):
  with pytest.raises(KeyError):
    del ctx['myvar']