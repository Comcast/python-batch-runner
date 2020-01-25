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
  """
  Captures framework-level configurations.
  
  The Config object is a data structure built for the purpose of
  receiving and prioritizing configurations from multiple sources.
  Configurations are taken from the first not-None source searched
  in the following order:
  
    1) Manually set value
    2) Environment variable
    3) Hard-coded default
  
  If accessing from with the a driver Python program, the below
  attributes are set/get in the same manner as a dictionary object.
  
  Attributes:
      app_name         : Unique name for application/job instance.
      app_start_time   : Start timestamp - not refreshed if restart from failure.
      app_root_dir     : Root dir path where config, log, temp, etc. dirs are located.
      config_dir       : Path to config directory.
      temp_dir         : Path to temp directory. Job checkpoint, state snapshots,
                         etc. are stored here.
      root_log_dir     : Path to the root log directory.
      log_dir          : Path to the log directory for current application/job instance.
                         By default, this will be <app_root_dir>/<YYYY-MM-DD>
      worker_dir       : Path to directory containing Python files implementing
                         Worker classes.
      nozip            : Execution option to turn off behavior that zips all log files
                         into a single .zip file after execution.
      dump_logs        : Execution option to turn onn behavior that prints out full
                         log contents to STDOUT for each failed Worker.
      email            : Execution option to specify email to send SUCCESS/FAILURE emails.
      debug            : Execution option to turn on more verbose output during execution.
      tickrate         : Execution option to specify the number of times per second the
                         engine should poll Workers. 1 by default.
      save_interval    : Execution option to specify the number of seconds between saving
                         job status and state to disk during execution. 10 by default
      max_procs        : Execution option to specify the maximum number of Workers
                         (processes) that may execute in parallel. No limit by default.
      log_retention    : Number of days to retain log files.
      dryrun           : Execution option to turn on 'dryrun', which prints out details
                         about the job to be executed.
      email_on_fail    : Execution option to turn on/off emails when job ends in failure.
      email_on_success : Execution option to turn on/off emails when job ends in success.
      test_mode        : Execution option to turn off specific features for unit tests.
  """
  
  def __init__(self):
    self._attr = {
      'app_name'         : { 'type': str , 'preserve': True,  'env': 'APP_NAME'            , 'value': None, 'default': "PyrunnerApp_{}".format(uuid.uuid4()) },
      'app_start_time'   : { 'type': str , 'preserve': True,  'env': None                  , 'value': None, 'default': None },
      'app_root_dir'     : { 'type': str , 'preserve': True,  'env': 'APP_ROOT_DIR'        , 'value': None, 'default': None },
      'config_dir'       : { 'type': str , 'preserve': True,  'env': 'APP_CONFIG_DIR'      , 'value': None, 'default': None },
      'temp_dir'         : { 'type': str , 'preserve': True,  'env': 'APP_TEMP_DIR'        , 'value': None, 'default': None },
      'log_dir'          : { 'type': str , 'preserve': True,  'env': 'APP_LOG_DIR'         , 'value': None, 'default': None },
      'root_log_dir'     : { 'type': str , 'preserve': True,  'env': 'APP_ROOT_LOG_DIR'    , 'value': None, 'default': None },
      'worker_dir'       : { 'type': str , 'preserve': True,  'env': 'APP_WORKER_DIR'      , 'value': None, 'default': None },
      'nozip'            : { 'type': bool, 'preserve': False, 'env': 'APP_NOZIP'           , 'value': None, 'default': False },
      'dump_logs'        : { 'type': bool, 'preserve': False, 'env': 'APP_DUMP_LOGS'       , 'value': None, 'default': False },
      'email'            : { 'type': str , 'preserve': False, 'env': 'APP_EMAIL'           , 'value': None, 'default': None },
      'debug'            : { 'type': bool, 'preserve': False, 'env': 'APP_DEBUG'           , 'value': None, 'default': False },
      'tickrate'         : { 'type': int , 'preserve': False, 'env': 'APP_TICKRATE'        , 'value': None, 'default': 1 },
      'save_interval'    : { 'type': int , 'preserve': False, 'env': 'APP_SAVE_INTERVAL'   , 'value': None, 'default': 10 },
      'max_procs'        : { 'type': int , 'preserve': False, 'env': 'APP_MAX_PROCS'       , 'value': None, 'default': -1 },
      'log_retention'    : { 'type': int , 'preserve': True,  'env': 'APP_LOG_RETENTION'   , 'value': None, 'default': 30 },
      'dryrun'           : { 'type': bool, 'preserve': False, 'env': 'APP_DRYRUN'          , 'value': None, 'default': False },
      'email_on_fail'    : { 'type': bool, 'preserve': False, 'env': 'APP_EMAIL_ON_FAIL'   , 'value': None, 'default': True },
      'email_on_success' : { 'type': bool, 'preserve': False, 'env': 'APP_EMAIL_ON_SUCCESS', 'value': None, 'default': True },
      'test_mode'        : { 'type': bool, 'preserve': True,  'env': 'APP_TEST_MODE'       , 'value': None, 'default': False }
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
    """
    Emulates dictionry key get action.
    
    Emulates the act of getting a key in a dictionary structure. Most importantly,
    keys in the Config object can receive it's value from one of multiple sources.
    
    The currently supported sources are: manually assigned values, environment variable
    values, and hard-coded default values, with priority matching this order.
    
    Args:
      key (str): The key name for which to return the value for.
    
    Raises:
      KeyError: Given key is not valid for the Config object.
    """
    detl = self._attr.get(key)
    if not detl:
      raise KeyError('Config object does not store key: {}'.format(key))
    
    attr_type = detl['type']
    # Priority 1: Manually provided value.
    if detl['value'] is not None:
      return attr_type(detl['value'])
    # Priority 2: Environment-variable-stored value.
    if detl['env'] and os.environ.get(detl['env']) is not None:
      if attr_type == bool and os.environ.get(detl['env'], 'TRUE').upper() == 'FALSE':
        return False
      return attr_type(os.environ.get(detl['env']))
    # Priority 3: Hard-coded default value.
    if detl['default'] is not None:
      return attr_type(detl['default'])
    
    return None
  
  def __setitem__(self, key, value):
    """
    Emulates dictionry key set action.
    
    Emulates the act of setting a key in a dictionary structure. Additionally,
    key names and variable values/types are validated upon set. If invalid key
    name or invalid value type, an exception will be thrown.
    
    Args:
      key (str): The key name for which to assign the incoming value to.
      value (mixed): The value to assign key with.
    
    Raises:
      KeyError: Given key is not valid for the Config object.
    """
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
    """
    Emulates dictionry key delete action.
    
    Emulates the act of deleting a key in a dictionary structure.
    
    Args:
      key (str): The key name for which to delete the current.
    
    Raises:
      KeyError: Given key is not valid for the Config object.
    """
    if key not in self._attr:
      raise KeyError('Config object does not store key: {}'.format(key))
    else:
      self._attr[key]['value'] = None
  
  def __contains__(self, key):
    """
    Determines if key is stored in the Config object.
    
    Args:
      key (str): The key name for which to check for existence.
    
    Returns:
      Boolean True/False indicating if key exists in Config.
    """
    return key in self._attr
  
  def items(self, only_preserve=True):
    """
    Converts the Config object into a simple dictionary containing only simple key:value pairs.
    
    Converts the internal representation of Config object and returns a simple dictionary
    containing each key and it's highest priority value currently assigned. Optionally allows
    for selection of only key:value pairs marked for preservation, rather than returning
    all pairs. By default, only returns preserved pairs.
    
    Preserved pairs aare those designated for persisting into longer term storage in case
    of job failure.
    
    Args:
      only_preserve (bool, optional): Indicates if only keys marked for preservation
        should be returned. Default: True
    
    Returns:
      Dictionary containing keys assigned with their highest priority value in Config object.
    """
    return { k:v['value'] for k,v in self._attr.items() if v['preserve'] }
  
  @property
  def ctllog_file(self):
    """
    Path/filename of job's .ctllog file.
    """
    if not self['temp_dir'] or not self['app_name']:
      return None
    else:
      return '{}/{}.ctllog'.format(self['temp_dir'], self['app_name'])
  
  @property
  def ctx_file(self):
    """
    Path/filename of job's .ctx file.
    """
    if not self['temp_dir'] or not self['app_name']:
      return None
    else:
      return '{}/{}.ctx'.format(self['temp_dir'], self['app_name'])
  
  def source_config_file(self, config_file):
    """
    Sources config file to export environment variables.
    
    Sources the given file in order to export environment variables
    prior to executing app/job instance. Only variables beginning with
    'APP_' will be preserved/exported, while other vars will be lost.
    
    Args:
      config_file (str): The path to the application profile/config to source.
    
    Raises:
      FileNotFoundError: Could not find specified file or is not a file.
    """
    # For compatability with older Python3 versions
    str_path = str(config_file)
    
    print('Sourcing File: {}'.format(str_path))
    if not str_path or not os.path.isfile(str_path):
      raise FileNotFoundError('Configuration file {} does not exist.'.format(str_path))
    
    # Source config file and print out all environment vars
    command = ['bash', '-c', 'source {} && env | grep ^APP_'.format(str_path)]
    proc = Popen(command, stdout = PIPE)
    
    # Set environment vars returned by process
    for line in proc.stdout:
      (key, _, value) = line.decode("utf-8").partition("=")
      os.environ[key] = value.rstrip()
    
    proc.communicate()
  
  def print_attributes(self):
    """
    Prints out the Contig object's key:value pairs, using the highest
    priority source as value.
    """
    for k in self._attr:
      print('{} : {}'.format(k, self._attr[k]))