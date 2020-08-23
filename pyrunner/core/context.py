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
import time
from subprocess import Popen, PIPE
from collections import deque

class Context:
  """
  Stores dictionary and queue objects to be shared across all processes.
  
  Accepts various forms of a dictionary and queue object. However, during
  normal execution, these will be multiprocessing.Manager data structures
  in order to allow data sharing across unique processes (within current
  app/job instance).
  
  Attributes are accessed in the same manner as attributes/values in a dict.
  
  Attributes:
    interactive: Boolean flag to specify if app is executed in 'interactive' mode.
  """
  
  def __init__(self, shared_dict, shared_queue):
    self.interactive = False
    self._shared_dict = shared_dict
    self._shared_queue = shared_queue
    self._iter_keys = None
    
    return
  
  # Dictionary emulation methods
  def __iter__(self):
    self._iter_keys = deque(self._shared_dict.keys())
    return self
  
  def __next__(self):
    if not self._iter_keys:
      raise StopIteration
    else:
      return self._iter_keys.popleft()
  
  def __getitem__(self, key):
    return self._shared_dict[key]
  
  def __setitem__(self, key, value):
    self._shared_dict[key] = value
  
  def __delitem__(self, key):
    del self._shared_dict[key]
  
  def __contains__(self, key):
    return key in self._shared_dict
  
  def items(self):
    return self._shared_dict.items()
  
  @property
  def shared_dict(self):
    return self._shared_dict
  @property
  def shared_queue(self):
    return self._shared_queue
  
  @property
  def keys(self):
    return self._shared_dict.keys()
  
  def has_key(self, key):
    return key in self._shared_dict
  
  def set(self, key, value):
    self._shared_dict[key] = value
    return
  
  def get(self, key, default=None):
    """
    Retrieves value for provided attribute, if any.
    
    Similar to the .get() method for a dict object. If 'interactive' is set
    to True and a non-existent attribute is requested, execution for the
    calling Worker will pause and wait for input from STDIN to use as
    the return value, instead of None.
    
    Returns:
      Stored value for key or value provided via STDIN if 'interactive'
      attribute is True. Otherwise None.
    """
    if self.interactive and not default and key not in self._shared_dict:
      self._shared_queue.put(key)
      while key not in self._shared_dict:
        time.sleep(0.5)
    
    return self._shared_dict.get(key, default)