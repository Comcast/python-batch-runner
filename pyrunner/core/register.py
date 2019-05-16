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
import pyrunner.core.constants as constants
from pyrunner.core.node import ExecutionNode

class NodeRegister:
  
  def __init__(self, serde, context=None):
    self._root = ExecutionNode(-1, 'PyRunnerRootNode')
    self.serde = serde
    self._context = context
    self._cur_node_id = 0
    self._register = {
      constants.STATUS_COMPLETED : set(),
      constants.STATUS_PENDING   : set(),
      constants.STATUS_RUNNING   : set(),
      constants.STATUS_FAILED    : set(),
      constants.STATUS_DEFAULTED : set(),
      constants.STATUS_NORUN     : set(),
      constants.STATUS_ABORTED   : set()
    }
    return
  
  @property
  def register(self):
    return self._register
  
  @property
  def context(self):
    return self._context
  @context.setter
  def context(self, value):
    self._context = value
    return self
  
  @property
  def completed_nodes(self):
    return self._register[constants.STATUS_COMPLETED]
  @property
  def completed_nodes_dict(self):
    return { n.id:n for n in self.completed_nodes }
  
  @property
  def pending_nodes(self):
    return self._register[constants.STATUS_PENDING]
  @property
  def pending_nodes_dict(self):
    return { n.id:n for n in self.pending_nodes }
  
  @property
  def running_nodes(self):
    return self._register[constants.STATUS_RUNNING]
  @property
  def running_nodes_dict(self):
    return { n.id:n for n in self.running_nodes }
  
  @property
  def failed_nodes(self):
    return self._register[constants.STATUS_FAILED]
  @property
  def failed_nodes_dict(self):
    return { n.id:n for n in self.failed_nodes }
  
  @property
  def defaulted_nodes(self):
    return self._register[constants.STATUS_DEFAULTED]
  @property
  def defaulted_nodes_dict(self):
    return { n.id:n for n in self.defaulted_nodes }
  
  @property
  def norun_nodes(self):
    return self._register[constants.STATUS_NORUN]
  @property
  def norun_nodes_dict(self):
    return { n.id:n for n in self.norun_nodes }
  
  @property
  def aborted_nodes(self):
    return self._register[constants.STATUS_ABORTED]
  @property
  def aborted_nodes_dict(self):
    return { n.id:n for n in self.aborted_nodes }
  
  @property
  def all_nodes(self):
    node_set = set()
    for grp in self._register:
      node_set = node_set.union(self._register[grp])
    return node_set
  @property
  def all_nodes_dict(self):
    return { n.id:n for n in self.all_nodes }
  
  def find_node(self, **kwargs):
    if kwargs.get('id'):
      return self._root.get_node_by_id(kwargs.get('id'))
    elif kwargs.get('name'):
      return self._root.get_node_by_name(kwargs.get('name'))
    else:
      return None
  
  def print_nodes(self):
    for bucket in self._register:
      for n in self._register[bucket]:
        print(n.id)
        print(n.name)
        print(n.module)
        print(n.worker)
        print(bucket)
        print()
    return
  
  def set_children_defaulted(self, node):
    stack = list(node.child_nodes)
    
    while stack:
      cur_node = stack.pop()
      if cur_node in self.pending_nodes:
        self.defaulted_nodes.add(cur_node)
        self.pending_nodes.remove(cur_node)
        stack.extend(list(cur_node.child_nodes))
    
    return
  
  def set_all_norun(self):
    self._register = {
      constants.STATUS_COMPLETED : set(),
      constants.STATUS_PENDING   : set(),
      constants.STATUS_RUNNING   : set(),
      constants.STATUS_FAILED    : set(),
      constants.STATUS_DEFAULTED : set(),
      constants.STATUS_NORUN     : self.all_nodes,
      constants.STATUS_ABORTED   : set()
    }
    return
  
  def exec_only(self, id_list):
    self.set_all_norun()
    
    for id in id_list:
      if id < 0:
        continue
      if id in self.norun_nodes_dict:
        n = self.norun_nodes_dict[id]
        self.norun_nodes.remove(n)
        self.pending_nodes.add(n)
    
    return
  
  def exec_to(self, id):
    self.set_all_norun()
    node = self.norun_nodes_dict.get(id)
    
    if id < 0 or not node:
      return
    
    run_set = { node }
    queue = list(node.parent_nodes)
    
    while queue:
      n = queue.pop(0)
      if n not in run_set and n.id >= 0:
        run_set.add(n)
        queue.extend(list(n.parent_nodes))
    
    self.norun_nodes.difference_update(run_set)
    self.pending_nodes.update(run_set)
    
    return
  
  def exec_from(self, id):
    if id < 0:
      return
    
    self.set_all_norun()
    node = self.norun_nodes_dict.get(id)
    
    if not node:
      return
    
    run_set = { node }
    queue = list(node.child_nodes)
    
    while queue:
      n = queue.pop(0)
      if n not in run_set and n.id >= 0:
        run_set.add(n)
        queue.extend(list(n.child_nodes))
    
    self.norun_nodes.difference_update(run_set)
    self.pending_nodes.update(run_set)
    
    return
  
  def exec_disable(self, id_list):
    for id in id_list:
      if id < 0:
        continue
      if id in self.pending_nodes_dict:
        n = self.pending_nodes_dict[id]
        self.pending_nodes.remove(n)
        self.norun_nodes.add(n)
    return
  
  def add_node_object(self, node, status, dependencies, named_deps=False):
    node.context = self._context
    self._root.add_child_node(node, dependencies, named_deps)
    if len(node.parent_nodes) != len(dependencies):
      return False
    self._register[status].add(node)
    return True
  
  def add_node(self, **kwargs):
    '''Add ExecutionNode object to the internal register.'''
    req_keys = ['name', 'logfile', 'module', 'worker']
    if not all(k in kwargs for k in req_keys):
      print('Missing Required Keys')
      return False
    
    self._cur_node_id += 1
    node = ExecutionNode(kwargs.get('id', self._cur_node_id))
    node.name = kwargs.get('name')
    node.module = kwargs.get('module')
    node.worker = kwargs.get('worker')
    
    if kwargs.get('logfile'):
      node.logfile = kwargs.get('logfile')
    if kwargs.get('argv'):
      node.arguments = kwargs.get('argv')
    if kwargs.get('arguments'):
      node.arguments = kwargs.get('arguments')
    if kwargs.get('retries'):
      node.max_attempts = kwargs.get('retries')
    if kwargs.get('retry_wait_time'):
      node.retry_wait_time = kwargs.get('retry_wait_time')
    
    return self.add_node_object(node, kwargs.get('status', constants.STATUS_PENDING), kwargs.get('dependencies', ['PyRunnerRootNode']), True)
  
  def load_from_file(self, proc_file, restart=False):
    if not os.path.isfile(proc_file):
      return False
    
    node_list = self.serde.deserialize(proc_file, restart)
    prev_count = len(node_list)
    
    while node_list.copy():
      temp = []
      for item in node_list:
        if not self.add_node_object(*item):
          temp.append(item)
      if prev_count == len(temp):
        raise RuntimeError('Could not resolve all parent IDs for {}'.format([ node.id for node,status,dependencies in temp ]))
      prev_count = len(temp)
      node_list = temp
    
    return True
  
  def save_to_file(self, filename, suppress_output=False):
    try:
      if not suppress_output:
        print('Saving Execution Graph File to: {}'.format(filename))
      
      node_list = []
      for grp in self._register:
        for node in self._register[grp]:
          node_list.append((node, grp))
      
      self.serde.save_to_file(filename, node_list)
    except Exception:
      print("Failure in save_to_file()")
      raise
    return filename