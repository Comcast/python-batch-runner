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

import pyrunner.core.constants as constants
from pyrunner.core.config import Config
from pyrunner.core.context import Context
from pyrunner.core.signal import SignalHandler, SIG_ABORT, SIG_PAUSE
from multiprocessing import Manager

import os, sys, glob
import time
import pickle

class ExecutionEngine:
  """
  The heart of all worker execution. Delegates state management of each
  ExecutionNode to the NodeRegister and triggers each node in the appropriate
  order.
  """
  
  def __init__(self):
    self.config = Config()
    self.register = None
    self.start_time = None
    self.save_state_func = lambda *args: None
    
    # Initialization of Manager proxy objects and Context
    self._manager = Manager()
    self._shared_dict = self._manager.dict()
    self._shared_queue = self._manager.Queue()
    self.context = Context(self._shared_dict, self._shared_queue)
  
  def initiate(self, **kwargs):
    """Begins the execution loop."""
    
    signal_handler = SignalHandler(self.config)
    sys.path.append(self.config['worker_dir'])
    self.start_time = time.time()
    wait_interval = 1.0/self.config['tickrate'] if self.config['tickrate'] >= 1 else 0
    last_save = 0
    ab_code = 0
    
    if not self.register: raise RuntimeError('NodeRegister has not been initialized!')
    
    # Execution loop
    try:
      while self.register.running_nodes or self.register.pending_nodes:
        sig_set = signal_handler.consume()
        
        # Check for abort signals
        if SIG_ABORT in sig_set:
          print('ABORT signal received! Terminating all running Workers.')
          self._abort_all_workers()
          return -1
        
        # Poll running nodes for completion/failure
        for node in self.register.running_nodes.copy():
          retcode = node.poll()
          if retcode is not None:
            self.register.running_nodes.remove(node)
            if retcode > 0:
              self.register.failed_nodes.add(node)
              self.register.set_children_defaulted(node)
            elif retcode < 0:
              self.register.pending_nodes.add(node)
            else:
              self.register.completed_nodes.add(node)
        
        # Check pending nodes for eligibility to execute
        for node in self.register.pending_nodes.copy():
          if self.config['max_procs'] > 0 and len(self.register.running_nodes) >= self.config['max_procs']:
            break
          
          runnable = True
          for p in node.parent_nodes:
            if p.id >= 0 and p not in self.register.completed_nodes.union(self.register.norun_nodes):
              runnable = False
              break
          if runnable:
            self.register.pending_nodes.remove(node)
            node.context = self.context
            node.execute()
            self.register.running_nodes.add(node)
        
        if not kwargs.get('silent'):
          self._print_current_state()
        
        # Check for input requests from interactive mode
        while self.context and self.context.shared_queue and not self.context.shared_queue.empty():
          key = self.context.shared_queue.get()
          value = input("Please provide value for '{}': ".format(key))
          self.context.set(key, value)
        
        # Persist state to disk at set intervals
        if not self.config['test_mode'] and self.save_state_func and (time.time() - last_save) >= self.config['save_interval']:
          self.save_state_func(True)
          last_save = time.time()
        
        # Wait
        if wait_interval > 0:
          time.sleep(wait_interval - ((time.time() - self.start_time) % wait_interval))
    except KeyboardInterrupt:
      print('\nKeyboard Interrupt Received')
      print('\nCancelling Execution')
      self._abort_all_workers()
      return -1
    
    if not kwargs.get('silent'):
      self._print_final_state(ab_code)
    
    if not self.config['test_mode'] and self.save_state_func:
      self.save_state_func()
    
    return len(self.register.failed_nodes)
  
  def _abort_all_workers(self):
    for node in self.register.running_nodes:
      node.terminate()
      #self.register.running_nodes.remove(node)
      #self.register.aborted_nodes.add(node)
      #self.register.set_children_defaulted(node)
  
  def _print_current_state(self):
    elapsed = time.time() - self.start_time
    
    if not self.config['debug']:
      print('Pending: {} | Running: {} | Completed: {} | Failed: {} | Defaulted: {} | Time Elapsed: {:0.2f} sec.'.format(
        len(self.register.pending_nodes),
        len(self.register.running_nodes),
        len(self.register.completed_nodes),
        len(self.register.failed_nodes),
        len(self.register.defaulted_nodes),
        elapsed
      ), flush=True)
    else:
      print(chr(27) + "[2J")
      print('Elapsed Time: {:0.2f}'.format(elapsed))
      if self.register.pending_nodes: print('\nPENDING TASKS')
      for p in self.register.pending_nodes:
        print('  {} - {}'.format(p.id, p.name))
      if (self.register.failed_nodes.union(self.register.defaulted_nodes)): print('\nFAILED TASKS')
      for p in self.register.failed_nodes.union(self.register.defaulted_nodes):
        print('  {} - {}'.format(p.id, p.name))
      if self.register.running_nodes: print('\nRUNNING TASKS')
      for p in self.register.running_nodes:
        print('  {} - {}'.format(p.id, p.name))
    
    return
  
  def _print_final_state(self, ab_code=0):
    print('\nCompleted in {:0.2f} seconds\n'.format(time.time() - self.start_time))
    
    if ab_code > 0:
      print('Final Status: ABORTED\n')
    elif len(self.register.failed_nodes) + len(self.register.defaulted_nodes):
      print('Final Status: FAILURE\n')
      print('Failed Processes:\n')
      
      for n in self.register.failed_nodes:
        print('ID: {}'.format(n.id))
        print('Name: {}'.format(n.name))
        print('Module: {}'.format(n.module))
        print('Worker: {}'.format(n.worker))
        print('Arguments: {}'.format(n.arguments))
        print('Log File: {}\n'.format(n.logfile))
      
      if self.config['dump_logs']:
        print('DUMPING FAILURE LOGS\n')
        
        for n in self.register.failed_nodes:
          print('############################################################################')
          print('# ID: {}'.format(n.id))
          print('# Name: {}'.format(n.name))
          print('# Module: {}'.format(n.module))
          print('# Worker: {}'.format(n.worker))
          print('# Arguments: {}'.format(n.arguments))
          print('# Log File: {}'.format(n.logfile))
          with open(n.logfile, 'r') as f:
            for line in f:
              print(line, end='')
      
    else:
      print('Final Status: SUCCESS\n')
    
    return