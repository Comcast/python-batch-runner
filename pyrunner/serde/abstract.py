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

from abc import ABCMeta, abstractmethod

class SerDe:
  __metaclass__ = ABCMeta
  
  @abstractmethod
  def serialize(self, node_register):
    pass
  
  @abstractmethod
  def deserialize(self):
    pass
  
  def is_named_deps(self):
    return False
  
  def save_to_file(self, filepath, node_list):
    try:
      with open(filepath, 'w') as file:
        file.write(self.serialize(node_list))
    except Exception:
      print('Failure in save_to_file()')
      raise