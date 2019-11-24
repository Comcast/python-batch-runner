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
from abc import ABCMeta, abstractmethod

class SerDe:
  """
  Implementations of this abstract class serve to translate between a
  NodeRegister and it's off-memory/persistant representation on the file system
  or elsewhere.
  """
  
  __metaclass__ = ABCMeta
  
  @abstractmethod
  def serialize(self, node_register):
    """
    This method must be implemented in the child class to translate a provided
    NodeRegister instance to it's target off-memory representation.
    """
    pass
  
  @abstractmethod
  def deserialize(self, proc_file, restart=False):
    """
    This method must be implemented in teh child class to translate it's
    off-memory representation to a NodeRegister instance.
    """
    pass
  
  def save_to_file(self, filepath, node_register):
    tmp  = filepath+'.tmp'
    perm = filepath
    
    try:
      with open(tmp, 'w') as file:
        file.write(self.serialize(node_register))
      if os.path.isfile(perm):
        os.unlink(perm)
      os.rename(tmp, perm)
    except Exception:
      print('Failure in save_to_file()')
      raise