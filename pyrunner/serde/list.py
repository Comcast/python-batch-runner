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

import os, re
import pyrunner.core.constants as constants
from pyrunner.serde.abstract import SerDe
from pyrunner.core.register import NodeRegister

class ListSerDe(SerDe):
  
  def deserialize(self, proc_file, restart=False):
    print('Processing Process List File: {}'.format(proc_file))
    if not proc_file or not os.path.isfile(proc_file):
      raise FileNotFoundError('Process file {} does not exist.'.format(proc_file))
    
    register = NodeRegister()
    pipe_pattern  = re.compile(r'''((?:[^|"']|"[^"]*"|'[^']*')+)''')
    comma_pattern = re.compile(r'''((?:[^,"']|"[^"]*"|'[^']*')+)''')
    
    with open(proc_file) as f:
      proc_list = f.read().splitlines()
    
    if not proc_list: raise ValueError('No information read from process list file')
    
    i = 0
    header = ''
    
    while not header:
      header = proc_list[i].strip()
      i += 1
    
    if header[0] != '#':
      raise RuntimeError('Missing execution mode header in process list file. Must have at minimum:\n#SHELL\nor\n#PYTHON')
      
    mode = header[1:].split('|')[0]
    
    if mode not in [ constants.MODE_SHELL, constants.MODE_PYTHON ]:
      raise RuntimeError('Incorrect execution mode in header: {}'.format(mode))
    
    used_ids = set()
    
    for proc in proc_list:
      proc = proc.strip()
      
      # Skip Comments and Empty Lines
      if not proc or proc[0] == '#':
        continue
      
      details = [ x.strip(' |') for x in pipe_pattern.split(proc)[1:-1] if x != '|' ]
      sub_details = []
      
      # Substitute $ENV{...} vars with environment vars.
      for item in details:
        if "$ENV{" in item:
          subbed = []
          disect = re.split(r"\$ENV|}", item)
          for x in disect:
            if x[:1] == '{':
              val = os.environ[x[1:]]
              subbed.append(val)
            else:
              subbed.append(x)
          sub_details.append(''.join(subbed))
        else:
          sub_details.append(item)
      
      id = int(sub_details[0])
      if id in used_ids:
        return False
      else:
        used_ids.add(id)
      
      dependencies = [ int(x) for x in sub_details[1].split(',') ]
      
      if mode == constants.MODE_SHELL:
        if restart:
          register.add_node(
            id = id,
            dependencies = dependencies,
            max_attempts = sub_details[2],
            retry_wait_time = sub_details[3],
            status = sub_details[4] if sub_details[4] in [ constants.STATUS_COMPLETED, constants.STATUS_NORUN ] else constants.STATUS_PENDING,
            name = sub_details[6],
            module = 'pyrunner',
            worker = 'ShellWorker',
            arguments = [sub_details[7]],
            logfile = sub_details[8] if len(sub_details) > 8 else None,
            named_deps = False
          )
        else:
          register.add_node(
            id = id,
            dependencies = dependencies,
            max_attempts = sub_details[2],
            retry_wait_time = sub_details[3],
            name = sub_details[4],
            module = 'pyrunner',
            worker = 'ShellWorker',
            arguments = [sub_details[5]],
            logfile = sub_details[6] if len(sub_details) > 6 else None,
            named_deps = False
          )
      else:
        if restart:
          register.add_node(
            id = id,
            dependencies = dependencies,
            max_attempts = sub_details[2],
            retry_wait_time = sub_details[3],
            status = sub_details[4] if sub_details[4] in [ constants.STATUS_COMPLETED, constants.STATUS_NORUN ] else constants.STATUS_PENDING,
            name = sub_details[6],
            module = sub_details[7],
            worker = sub_details[8],
            arguments = [ s.strip('"') if s.strip().startswith('"') and s.strip().endswith('"') else s.strip() for s in comma_pattern.split(sub_details[9])[1::2] ] if len(sub_details) > 9 else None,
            logfile = sub_details[10] if len(sub_details) > 10 else None,
            named_deps = False
          )
        else:
          register.add_node(
            id = id,
            dependencies = dependencies,
            max_attempts = sub_details[2],
            retry_wait_time = sub_details[3],
            name = sub_details[4],
            module = sub_details[5],
            worker = sub_details[6],
            arguments = [ s.strip('"') if s.strip().startswith('"') and s.strip().endswith('"') else s.strip() for s in comma_pattern.split(sub_details[7])[1::2] ] if len(sub_details) > 7 else None,
            logfile = sub_details[8] if len(sub_details) > 8 else None,
            named_deps = False
          )
    
    return register
  
  def get_ctllog_line(self, node, status):
      parent_id_list = [ str(x.id) for x in node.parent_nodes ]
      parent_id_str = ','.join(parent_id_list) if parent_id_list else '-1'
      return "{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}".format(node.id, parent_id_str, str(node.max_attempts), str(node.retry_wait_time), status, node.get_elapsed_time(), node.name, node.module, node.worker, ','.join(node.arguments), node.logfile)
      
  def serialize(self, register):
    node_list = []
    for grp in register.register:
      for node in register.register[grp]:
        node_list.append((node, grp))
    node_list.sort(key = (lambda n : n[0].id))
    return '{}\n\n'.format(constants.HEADER_PYTHON) + '\n'.join([ self.get_ctllog_line(node, status) for node,status in node_list ])