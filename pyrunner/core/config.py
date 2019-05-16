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
import uuid
from subprocess import Popen, PIPE
from collections import deque

class Config:

  def __init__(self):
    self._attr = {
      'app_name'         : { 'type': str , 'env': 'APP_NAME'            , 'value': None, 'default': "PyrunnerApp_{}".format(uuid.uuid4()) },
      'app_start_time'   : { 'type': str , 'env': None                  , 'value': None, 'default': None },
      'app_root_dir'     : { 'type': str , 'env': 'APP_ROOT_DIR'        , 'value': None, 'default': None },
      'config_dir'       : { 'type': str , 'env': 'APP_CONFIG_DIR'      , 'value': None, 'default': None },
      'temp_dir'         : { 'type': str , 'env': 'APP_TEMP_DIR'        , 'value': None, 'default': None },
      'log_dir'          : { 'type': str , 'env': 'APP_LOG_DIR'         , 'value': None, 'default': None },
      'root_log_dir'     : { 'type': str , 'env': 'APP_ROOT_LOG_DIR'    , 'value': None, 'default': None },
      'worker_dir'       : { 'type': str , 'env': 'APP_WORKER_DIR'      , 'value': None, 'default': None },
      'nozip'            : { 'type': bool, 'env': 'APP_NOZIP'           , 'value': None, 'default': False },
      'dump_logs'        : { 'type': bool, 'env': 'APP_DUMP_LOGS'       , 'value': None, 'default': False },
      'email'            : { 'type': str , 'env': 'APP_EMAIL'           , 'value': None, 'default': None },
      'debug'            : { 'type': bool, 'env': 'APP_DEBUG'           , 'value': None, 'default': False },
      'tickrate'         : { 'type': int , 'env': 'APP_TICKRATE'        , 'value': None, 'default': 1 },
      'save_interval'    : { 'type': int , 'env': 'APP_SAVE_INTERVAL'   , 'value': None, 'default': 10 },
      'max_procs'        : { 'type': int , 'env': 'APP_MAX_PROCS'       , 'value': None, 'default': -1 },
      'log_retention'    : { 'type': int , 'env': 'APP_LOG_RETENTION'   , 'value': None, 'default': 30 },
      'dryrun'           : { 'type': bool, 'env': 'APP_DRYRUN'          , 'value': None, 'default': False },
      'email_on_fail'    : { 'type': bool, 'env': 'APP_EMAIL_ON_FAIL'   , 'value': None, 'default': True },
      'email_on_success' : { 'type': bool, 'env': 'APP_EMAIL_ON_SUCCESS', 'value': None, 'default': True },
      'test_mode'        : { 'type': bool, 'env': 'APP_TEST_MODE'       , 'value': None, 'default': False }
    }
    self._iter_keys = None
  
  def __iter__(self):
    self._iter_keys = deque(self._attr.keys())
    return self
  
  def __next__(self):
    if not self._iter_keys:
      raise StopIteration
    else:
      return self._iter_keys.popleft()
  
  def __getitem__(self, key):
    detl = self._attr.get(key)
    if not detl:
      raise KeyError('Config object does not store key: {}'.format(key))
    
    attr_type = detl['type']
    if detl['value'] is not None:
      return attr_type(detl['value'])
    if detl['env'] and os.environ.get(detl['env']) is not None:
      if attr_type == bool and os.environ.get(detl['env']) == 'FALSE':
        return False
      return attr_type(os.environ.get(detl['env']))
    if detl['default'] is not None:
      return attr_type(detl['default'])
    
    return None
  
  def __setitem__(self, key, value):
    if key not in self._attr:
      raise KeyError('Config object does not store key: {}'.format(key))
    else:
      if value is None:
        self._attr[key]['value'] = None
      elif self._attr[key]['type'] == bool and isinstance(value, str):
        if value.upper().strip() == 'FALSE':
          self._attr[key]['value'] = False
        elif value.upper().strip() == 'TRUE':
          self._attr[key]['value'] = True
        else:
          self._attr[key]['value'] = self._attr[key]['type'](value)
      else:
        self._attr[key]['value'] = self._attr[key]['type'](value)
  
  def __delitem__(self, key):
    if key not in self._attr:
      raise KeyError('Config object does not store key: {}'.format(key))
    else:
      self._attr[key]['value'] = None
  
  def __contains__(self, key):
    return key in self._attr
  
  def items(self):
    return { k:v['value'] for k,v in self._attr.items() }
  
  @property
  def ctllog_file(self):
    if not self['temp_dir'] or not self['app_name']:
      return None
    else:
      return '{}/{}.ctllog'.format(self['temp_dir'], self['app_name'])
  
  @property
  def ctx_file(self):
    if not self['temp_dir'] or not self['app_name']:
      return None
    else:
      return '{}/{}.ctx'.format(self['temp_dir'], self['app_name'])
  
  def source_config_file(self, config_file):
    print('Sourcing File: {}'.format(config_file))
    if not config_file or not os.path.isfile(config_file):
      raise FileNotFoundError('Configuration file {} does not exist.'.format(config_file))
    
    # Source config file and print out all environment vars
    command = ['bash', '-c', 'source {} && env | grep ^APP_'.format(config_file)]
    proc = Popen(command, stdout = PIPE)
    
    # Set environment vars returned by process
    for line in proc.stdout:
      (key, _, value) = line.decode("utf-8").partition("=")
      os.environ[key] = value.rstrip()
    
    proc.communicate()
  
  def print_attributes(self):
    for k in self._attr:
      print('{} : {}'.format(k, self._attr[k]))
    return