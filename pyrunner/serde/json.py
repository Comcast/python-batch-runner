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

import os, re, json
import pyrunner.core.constants as constants
from pyrunner.serde.abstract import SerDe
from pyrunner.core.register import NodeRegister

class JsonSerDe(SerDe):
  
  def deserialize(self, proc_file, restart=False):
    print('Processing Process JSON File: {}'.format(proc_file))
    if not proc_file or not os.path.isfile(proc_file):
      raise FileNotFoundError('Process file {} does not exist.'.format(proc_file))
    
    register = NodeRegister()
    proc_obj = json.load(proc_file)
    used_names = set()
    
    for name,details in proc_obj.items():
      if name in used_names:
        raise RuntimeError('Task name {} has already been registered'.format(name))
      else:
        used_names.add(name)
      
      # Substitute $ENV{...} vars with environment vars.
      sub_details = dict()
      for k,v in details.items():
        if "$ENV{" in v:
          subbed = []
          disect = re.split(r"\$ENV|}", v)
          for x in disect:
            if x[:1] == '{':
              val = os.environ[x[1:]]
              subbed.append(val)
            else:
              subbed.append(x)
          sub_details[k] = ''.join(subbed)
        else:
          sub_details[k] = v
      
      register.add_node(name = name, **sub_details)
      
    return register
  
  def serialize(self, register):
    obj = { 'tasks' : dict() }
    for node in sorted(register.all_nodes, key = (lambda n : n.id)):
      obj['tasks'][node.name] = {
        'module'  : node.module,
        'worker'  : node.worker,
        'logfile' : node.logfile
      }
      if not (len(node.parent_nodes()) == 1 and node.parent_nodes().pop().name == constants.ROOT_NODE_NAME):
        obj['tasks'][node.name]['dependencies'] = [ p.name for p in node.parent_nodes() ]
      if node.max_attempts > 1:
        obj['tasks'][node.name]['max_attempts'] = node.max_attempts
        obj['tasks'][node.name]['retry_wait_time'] = node.retry_wait_time
      if node.arguments:
        obj['tasks'][node.name]['arguments'] = node.arguments
    
    return json.dumps(obj)