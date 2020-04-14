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
import pyrunner.logger.file as lg
from pyrunner.worker.abstract import Worker

import os, sys
import time
import multiprocessing
import importlib
import traceback
import inspect

from time import gmtime, strftime

class ExecutionNode:
  """
  The 'mechanical' representation of a Worker. The Node is responsible for
  instantiating the user-defined worker and managing its execution at runtime.
  
  Each Node maintains a reference to it's parent and child nodes, in addition
  to a variety of runtime statistics/state information.
  """
  
  def __init__(self, id=-1, name=None):
    if int(id) < -1:
      raise ValueError('id must be -1 or greater')
    if name:
      self.name = name
    
    self._id = int(id)
    
    # Num attempts/restart management
    self._attempts = 0
    self._max_attempts = 1
    self._retry_wait_time = 0
    self._wait_until = 0
    
    self._start_time = 0
    self._end_time = 0
    self._timeout = float('inf')
    self._proc = None
    self._context = None
    
    self._module = None
    self._worker = None
    self._worker_instance = None
    
    self._parent_nodes = set()
    self._child_nodes = set()
    
    return
  
  def __hash__(self):
    return hash(self._id)
  def __eq__(self, other):
    return self._id == other._id
  def __ne__(self, other):
    return not (self._id == other._id)
  def __lt__(self, other):
    return self._id < other._id
  
  def is_runnable(self):
    return time.time() >= self._wait_until
  
  def execute(self):
    """
    Spawns a new process via the `run` method of defined Worker class.
    
    Utilizes multiprocessing's Process to fork a new process to execute the `run` method implemented
    in the provided Worker class.
    
    Workers are given references to the shared Context, main-proc <-> child-proc return code value,
    logfile handle, and task-level arguments.
    """
    # Return early if retry triggered and wait time has not yet fully elapsed
    if not self.is_runnable():
      return
    
    self._attempts += 1
    
    if not self._start_time:
      self._start_time = time.time()
    
    try:
      # Check if provided worker actually extends the Worker class.
      if not issubclass(self.worker_class, Worker):
        raise TypeError('{}.{} is not an extension of pyrunner.Worker'.format(self.module, self.worker))
      
      # Launch the "run" method of the provided Worker under a new process.
      self._worker_instance = self.worker_class(self.context, self.logfile, self.argv)
      self._proc = multiprocessing.Process(target=self._worker_instance.protected_run, daemon=False)
      self._proc.start()
    except Exception as e:
      logger = lg.FileLogger(self.logfile)
      logger.open()
      logger.error(str(e))
      logger.close()
    
    return
  
  def poll(self, wait=False):
    """
    Polls the running process for completion and returns the worker's return code. None if still running.
    
    Args:
      wait (bool): If enabled (set to True), the `poll` method will be a blocking call.
                   If False (default behavior), the method will not wait until the completion
                   of the child process and return `None`, if proc is still running.
    
    Returns:
      Integer return code if process has exited, otherwise `None`.
    """
    if not self._proc:
      return 905
    
    running = self._proc.is_alive()
    retcode = 0
    
    if not running or wait:
      # Note that if wait is True, then the join() method is invoked immediately,
      # causing the thread to block until it's job is complete.
      self._proc.join()
      self._end_time = time.time()
      retcode = self._worker_instance.retcode
      if retcode > 0 and (self._attempts < self.max_attempts):
        logger = lg.FileLogger(self.logfile)
        logger.open(False)
        self._wait_until = time.time() + self._retry_wait_time
        logger.restart_message(self._attempts, 'Waiting {} seconds before retrying...'.format(self._retry_wait_time))
        logger.close(False)
        retcode = -1
      self.cleanup()
    elif (time.time() - self._start_time) >= self._timeout:
      retcode = self.terminate('Worker runtime has exceeded the set maximum/timeout of {} seconds.'.format(self._timeout))
      running = False
    
    return retcode if (not running or wait) else None
  
  def terminate(self, message='Terminating process'):
    """
    Immediately terminates the Worker, if running.
    """
    if self._proc.is_alive():
      self._proc.terminate()
      logger = lg.FileLogger(self.logfile)
      logger.open(False)
      logger._system_(message)
      logger.close()
    self.cleanup()
    return 907
  
  def cleanup(self):
    self._proc = None
    self._context = None
    self._worker_instance = None
  
  
  # ########################## MISC ########################## #
  
  def get_node_by_id(self, id):
    if self._id == id:
      return self
    elif not self._child_nodes:
      return None
    else:
      for n in self._child_nodes:
        temp = n.get_node_by_id(id)
        if temp:
          return temp
    return None
  
  def get_node_by_name(self, name):
    if self._name == name:
      return self
    elif not self._child_nodes:
      return None
    else:
      for n in self._child_nodes:
        temp = n.get_node_by_name(name)
        if temp:
          return temp
    return None
  
  def add_parent_node(self, parent):
    self._parent_nodes.add(parent)
    return
  
  def add_child_node(self, child, parent_id_list, named_deps=False):
    if (named_deps and self._name in [ x for x in parent_id_list ]) or (not named_deps and self._id in [ int(x) for x in parent_id_list ]):
      child.add_parent_node(self)
      self._child_nodes.add(child)
    for c in self._child_nodes:
      c.add_child_node(child, parent_id_list, named_deps)
    return
  
  def pretty_print(self, indent=''):
    print('{}{} - {}'.format(indent, self._id, self._name))
    for c in self._child_nodes:
      c.pretty_print('{}  '.format(indent))
    return
  
  def get_elapsed_time(self):
    end_time = self._end_time if self._end_time else time.time()
    
    if self._start_time and end_time and end_time > self._start_time:
      elapsed_time = end_time - self._start_time
      return time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
    else:
      return '00:00:00'
  
  
  # ########################## SETTERS + GETTERS ########################## #
  
  def _validate_string(self, name, value, nullable=False):
    try:
      if nullable and value.strip() in ['', None]:
        return
      str(value)
    except:
      raise ValueError('Provided value is not castable to string')
    if not value or not str(value).strip():
      raise ValueError('{} cannot be None, blank, or only spaces'.format(name))
  
  @property
  def id(self):
    return getattr(self, '_id', -1)
  @id.setter
  def id(self, value):
    if int(value) < -1:
      raise ValueError('id must be -1 or greater')
    self._id = int(value)
    return self
  
  @property
  def name(self):
    return getattr(self, '_name', None)
  @name.setter
  def name(self, value):
    self._validate_string('name', value)
    self._name = str(value).strip()
    return self
  
  @property
  def context(self):
    return getattr(self, '_context', None)
  @context.setter
  def context(self, value):
    self._context = value
    return self
  
  @property
  def logfile(self):
    return getattr(self, '_logfile', None)
  @logfile.setter
  def logfile(self, value):
    if value.strip() == '':
      value = None
    self._validate_string('logfile', value, True)
    self._logfile = str(value).strip()
    return self
  
  @property
  def module(self):
    return getattr(self, '_module', None)
  @module.setter
  def module(self, value):
    self._validate_string('module', value)
    self._module = str(value).strip()
    return self
  
  @property
  def worker(self):
    return getattr(self, '_worker', None)
  @worker.setter
  def worker(self, value):
    self._validate_string('worker', value)
    self._worker = str(value).strip()
    return self
  
  @property
  def arguments(self):
    return getattr(self, '_argv', [])
  @arguments.setter
  def arguments(self, value):
    self._argv = [ str(x) for x in value ] if value else []
    return self
  
  @property
  def argv(self):
    return getattr(self, '_argv', [])
  @argv.setter
  def argv(self, value):
    self._argv = [ str(x) for x in value ] if value else []
    return self
  
  @property
  def max_attempts(self):
    return getattr(self, '_max_attempts', 1)
  @max_attempts.setter
  def max_attempts(self, value):
    if int(value) < 1:
      raise ValueError('max_attempts must be >= 1')
    self._max_attempts = int(value)
    return self
  
  @property
  def retry_wait_time(self):
    return getattr(self, '_retry_wait_time', 0)
  @retry_wait_time.setter
  def retry_wait_time(self, value):
    if int(value) < 0:
      raise ValueError('retry_wait_time must be >= 0')
    self._retry_wait_time = int(value)
    return self
  
  @property
  def timeout(self):
    return getattr(self, '_timeout', float('inf'))
  @timeout.setter
  def timeout(self, value):
    if int(value) < 1:
      raise ValueError('timeout must be greater than 0')
    self._timeout = int(value)
    return self
  
  @property
  def parent_nodes(self):
    return self._parent_nodes
  @property
  def child_nodes(self):
    return self._child_nodes
  
  @property
  def worker_class(self):
    return getattr(importlib.import_module(self.module), self.worker)