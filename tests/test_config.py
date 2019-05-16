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
from pathlib import Path
from datetime import datetime

from pyrunner.core.config import Config

abs_dir_path = os.path.dirname(os.path.realpath(__file__))

@pytest.fixture
def cfg_file():
  return '{}/config/test_profile'.format(abs_dir_path)

@pytest.fixture
def cfg():
  '''Returns a Config object loaded with test_profile'''
  cfg = Config()
  cfg.source_config_file('{}/config/test_profile'.format(abs_dir_path))
  return cfg

def test_source_config_file_env(cfg):
  env = os.environ
  assert (
    (env.get('APP_NAME')              == 'TestApplication')
    and (env.get('APP_ROOT_DIR')      == abs_dir_path)
    and (env.get('APP_CONFIG_DIR')    == '{}/config'.format(abs_dir_path))
    and (env.get('APP_TEMP_DIR')      == '{}/temp'.format(abs_dir_path))
    and (env.get('APP_DATA_DIR')      == '{}/data'.format(abs_dir_path))
    and (env.get('APP_ROOT_LOG_DIR')  == '{}/logs'.format(abs_dir_path))
    and (env.get('APP_WORKER_DIR')    == '{}/python'.format(abs_dir_path))
    and (env.get('APP_LOG_RETENTION') == '1')
    and (env.get('APP_LOG_DIR')       == '{}/logs/{}'.format(abs_dir_path, datetime.now().strftime('%Y-%m-%d')))
  )

def test_source_config_file_attr(cfg):
  assert (
    (cfg['app_name']          == 'TestApplication')
    and (cfg['app_root_dir']  == abs_dir_path)
    and (cfg['temp_dir']      == '{}/temp'.format(abs_dir_path))
    and (cfg['root_log_dir']  == '{}/logs'.format(abs_dir_path))
    and (cfg['log_retention'] == 1)
    and (cfg['worker_dir']    == '{}/python'.format(abs_dir_path))
    and (cfg['log_dir']       == '{}/logs/{}'.format(abs_dir_path, datetime.now().strftime('%Y-%m-%d')))
  )

def test_config_modify_attr(cfg):
  cfg['app_name']     = 'SomeWildName'
  cfg['app_root_dir'] = '/my/root/directory'
  cfg['log_dir']      = '/i/can/be/elsewhere'
  assert (
    (cfg['app_name']          == 'SomeWildName')
    and (cfg['app_root_dir']  == '/my/root/directory')
    and (cfg['log_dir']       == '/i/can/be/elsewhere')
  )

def test_attribute_error(cfg):
  with pytest.raises(AttributeError):
    cfg.unreal_var

def test_attribute_key_error(cfg):
  with pytest.raises(KeyError):
    cfg['unreal_var']

def test_attr_precedence(cfg_file):
  cfg = Config()
  cfg['app_name'] = 'ModifiedApplicationName'
  cfg['log_retention'] = 999
  
  cfg.source_config_file(cfg_file)
  
  assert (
    (cfg['app_name']          == 'ModifiedApplicationName')
    and (cfg['app_root_dir']  == abs_dir_path)
    and (cfg['temp_dir']      == '{}/temp'.format(abs_dir_path))
    and (cfg['root_log_dir']  == '{}/logs'.format(abs_dir_path))
    and (cfg['log_retention'] == 999)
    and (cfg['worker_dir']    == '{}/python'.format(abs_dir_path))
    and (cfg['log_dir']       == '{}/logs/{}'.format(abs_dir_path, datetime.now().strftime('%Y-%m-%d')))
  )

@pytest.mark.parametrize('value, err', [
  ('asdf', ValueError),
  ('', ValueError),
  (datetime.now(), TypeError),
  (datetime, TypeError)
])
def test_attr_int_raise_errors(cfg, value, err):
  with pytest.raises(err):
    cfg['tickrate'] = value

@pytest.mark.parametrize('key, set_value, expected', [
  ('app_name', 'NameToUnset', 'TestApplication'),
  ('nozip', True, False),
  ('max_procs', 5, -1)
])
def test_set_and_del(cfg, key, set_value, expected):
  cfg[key] = set_value
  del cfg[key]
  assert cfg[key] == expected

@pytest.mark.parametrize('key, set_value, expected', [
  ('app_name', 'NameToUnset', 'TestApplication'),
  ('nozip', True, False),
  ('max_procs', 5, -1)
])
def test_set_none(cfg, key, set_value, expected):
  cfg[key] = set_value
  cfg[key] = None
  assert cfg[key] == expected

@pytest.mark.parametrize('key, value, expected_type', [
  ('app_name', 'ThisShouldBeString', str),
  ('app_name', 1234, str),
  ('nozip', 'asdf', bool),
  ('nozip', 0, bool),
  ('nozip', '0', bool),
  ('nozip', '', bool),
  ('nozip', True, bool),
  ('nozip', False, bool),
  ('max_procs', 0, int),
  ('max_procs', '99', int),
  ('max_procs', 1.01, int)
])
def test_type_casting(cfg, key, value, expected_type):
  cfg[key] = value
  assert isinstance(cfg[key], expected_type)

@pytest.mark.parametrize('value, expected', [
  (True, True),
  (False, False),
  ('', False),
  (None, False),
  ('TrUe', True),
  ('FaLsE', False),
  ('fals', True),
  (0, False),
  (1, True),
  ('hello', True)
])
def test_bool_casting(cfg, value, expected):
  cfg['nozip'] = value
  assert cfg['nozip'] == expected