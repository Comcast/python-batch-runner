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

import os, sys
import glob
import shutil
import zipfile

import pyrunner.serde as serde
import pyrunner.notification as notification
import pyrunner.autodoc.introspection as intro
import pyrunner.core.constants as constants

from pyrunner.core.engine import ExecutionEngine
from pyrunner.core.config import Config
from pyrunner.core.context import Context
from pyrunner.core.register import NodeRegister
from pyrunner.version import __version__

from datetime import datetime as datetime
from multiprocessing import Manager
import pickle
import time

class PyRunner:
  
  def __init__(self, **kwargs):
    self.config = Config()
    self.notification = notification.EmailNotification()
    
    # Initialization of Manager proxy objects and Context
    self._manager = Manager()
    self._shared_dict = self._manager.dict()
    self._shared_queue = self._manager.Queue()
    self.context = Context(self._shared_dict, self._shared_queue)
    
    self.register = NodeRegister(serde.ListSerDe(), self.context)
    
    # NodeRegister wiring
    self.add_node      = self.register.add_node
    self.exec_only     = self.register.exec_only
    self.exec_to       = self.register.exec_to
    self.exec_from     = self.register.exec_from
    self.exec_disable  = self.register.exec_disable
    self.load_workflow = self.register.load_from_file
    
    # Config wiring
    self.source_config_file = self.config.source_config_file
    
    # Backwards compatability
    self.load_proc_list_file = self.register.load_from_file
    self.load_last_failed = self.load_state
  
  @property
  def version(self):
    return __version__
  @property
  def log_dir(self):
    return self.config['log_dir']
  
  def plugin_serde(self, obj):
    if not isinstance(obj, serde.SerDe): raise Exception('SerDe plugin must implement the SerDe interface')
    self.register = NodeRegister(obj)
  
  def plugin_notification(self, obj):
    if not isinstance(obj, notification.Notification): raise Exception('Notification plugin must implement the Notification interface')
    self.notification = obj
  
  def execute(self):
    return self.run()
  def run(self):
    self.config['app_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    engine = ExecutionEngine()
    engine.config = self.config
    engine.context = self.context
    engine.register = self.register
    engine.save_state_func = self.save_state
    
    if self.config['dryrun']:
      self.print_documentation()
      return 0
    
    print('Executing PyRunner App: {}'.format(self.config['app_name']))
    retcode = engine.initiate()
    
    if retcode == 0 and not self.config['email_on_success']:
      print('Skipping Email Notification: Property "email_on_success" is set to FALSE.')
    elif retcode != 0 and not self.config['email_on_fail']:
      print('Skipping Email Notification: Property "email_on_fail" is set to FALSE.')
    else:
      self.notification.emit_notification(self.config, self.register)
    
    if not self.config['nozip']:
      self.zip_log_files(retcode)
    
    self.cleanup_log_files()
    
    if retcode == 0:
      self.delete_state()
    
    return retcode
  
  def print_documentation(self):
    while self.register.pending_nodes:
      for node in self.register.pending_nodes.copy():
        runnable = True
        for p in node.parent_nodes:
          if p.id >= 0 and p not in self.register.completed_nodes.union(self.register.norun_nodes):
            runnable = False
            break
        if runnable:
          self.register.pending_nodes.remove(node)
          intro.print_context_usage(node)
          self.register.completed_nodes.add(node)
  
  def cleanup_log_files(self):
    if self.config['log_retention'] < 0:
      return
    
    try:
      
      files = glob.glob('{}/*'.format(self.config['root_log_dir']))
      to_delete = [ f for f in files if os.stat(f).st_mtime < (time.time() - (self.config['log_retention'] * 86400.0)) ]
      
      if to_delete:
        print('Cleaning Up Old Log Files')
      
      for f in to_delete:
        print('Deleting File/Directory: {}'.format(f))
        shutil.rmtree(f)
    except Exception:
      print("Failure in cleanup_log_files()")
      raise
    
    return
  
  def zip_log_files(self, exit_status):
    node_list = list(self.register.all_nodes)
    zf = None
    zip_file = None
    
    try:
      
      suffix = 'FAILURE' if exit_status else 'SUCCESS'
      
      zip_file = "{}/{}_{}_{}.zip".format(self.config['log_dir'], self.config['app_name'], constants.EXECUTION_TIMESTAMP, suffix)
      print('Zipping Up Log Files to: {}'.format(zip_file))
      zf = zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED)
      
      for node in node_list:
        if (node.id != -1 and node not in self.register.pending_nodes.union(self.register.defaulted_nodes)):
          logfile = node.logfile
          if os.path.isfile(logfile):
            zf.write(logfile, os.path.basename(logfile))
            os.remove(logfile)
      
      zf.write(self.config.ctllog_file, os.path.basename(self.config.ctllog_file))
      
    except Exception:
      print("Failure in zip_log_files()")
      raise
    finally:
      if zf:
        zf.close()
    
    return zip_file
  
  def save_state(self, suppress_output=False):
    self.register.save_to_file(self.config.ctllog_file, suppress_output)
    
    try:
      
      state_obj = {
        'config'       : self.config.items(),
        'shared_dict'  : self._shared_dict.copy()
      }
      
      if not suppress_output:
        print('Saving Context Object to File: {}'.format(self.config.ctx_file))
      pickle.dump(state_obj, open(self.config.ctx_file, 'wb'))
      
    except Exception:
      print("Failure in save_context()")
      raise
    
    return
  
  def load_state(self):
    if not self.register.load_from_file(self.config.ctllog_file, True):
      return False
    
    if not os.path.isfile(self.config.ctx_file):
      return False
    
    print('Loading prior Context from {}'.format(self.config.ctx_file))
    state_obj = pickle.load(open(self.config.ctx_file, 'rb'))
    
    for k,v in state_obj['config'].items():
      self.config[k] = v
    
    for k,v in state_obj['shared_dict'].items():
      self._shared_dict[k] = v
    
    return True
  
  def delete_state(self):
    if os.path.isfile(self.config.ctllog_file):
      os.remove(self.config.ctllog_file)
    if os.path.isfile(self.config.ctx_file):
      os.remove(self.config.ctx_file)