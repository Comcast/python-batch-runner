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
    """
    Returns a NodeRegister represented by the contents of provided JSON file.
    
    The root object is expected to have at least a 'task' attribute, whose
    value is an inner object keyed on the Task Name. Each Task Name is additionally
    an inner object with at minimum the 'module' and 'worker' attributes.
    
    See <URL here> for JSON file specifications.
    
    Args:
      proc_file (str): The path string for the JSON file containing a valid
        Execution Graph representation.
      restart (bool, optional): Flag to indicate if input file is a restart file.
        Default: False
    
    Returns:
      A NodeRegister representation of the Execution Graph in the JSON file.
    """
    
    print('Processing Process JSON File: {}'.format(proc_file))
    if not proc_file or not os.path.isfile(proc_file):
      raise FileNotFoundError('Process file {} does not exist.'.format(proc_file))
    
    register = NodeRegister()
    with open(proc_file) as f:
      proc_obj = json.load(f)
    used_names = set()
    
    for name,details in proc_obj['tasks'].items():
      if name in used_names:
        raise RuntimeError('Task name {} has already been registered'.format(name))
      else:
        used_names.add(name)
      
      # Substitute $ENV{...} vars with environment vars.
      sub_details = dict()
      for k,v in details.items():
        if "$ENV{" in str(v):
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
      if not (len(node.parent_nodes) == 1 and tuple(node.parent_nodes)[0].name == constants.ROOT_NODE_NAME):
        obj['tasks'][node.name]['dependencies'] = [ p.name for p in node.parent_nodes ]
      if node.max_attempts > 1:
        obj['tasks'][node.name]['max_attempts'] = node.max_attempts
        obj['tasks'][node.name]['retry_wait_time'] = node.retry_wait_time
      if node.arguments:
        obj['tasks'][node.name]['arguments'] = node.arguments
    
    return json.dumps(obj)