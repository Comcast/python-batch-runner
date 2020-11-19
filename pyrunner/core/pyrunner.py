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
import getopt
import traceback

import pyrunner.serde as serde
import pyrunner.notification as notification
import pyrunner.autodoc.introspection as intro
import pyrunner.core.constants as constants

from pyrunner.core.engine import ExecutionEngine
from pyrunner.core.config import Config
from pyrunner.core.register import NodeRegister
from pyrunner.core.signal import SignalHandler, SIG_ABORT, SIG_PAUSE, SIG_PULSE
from pyrunner.version import __version__

from pyrunner.notification import Notification

from datetime import datetime as datetime
import pickle
import time

class PyRunner:
  
  def __init__(self, **kwargs):
    self._environ = os.environ.copy()
    self.config = Config()
    self._notification = notification.EmailNotification()
    self.signal_handler = SignalHandler(self.config)
    
    self.serde_obj = serde.ListSerDe()
    self.register = NodeRegister()
    self.engine = ExecutionEngine()
    
    self.config['config_file'] = kwargs.get('config_file')
    self.config['proc_file'] = kwargs.get('proc_file')
    self.config['restart'] = kwargs.get('restart', False)
    
    self.parse_args(kwargs.get('parse_args', True))
    
    if self.dup_proc_is_running():
      raise OSError('Another process for "{}" is already running!'.format(self.config['app_name']))
    else:
      # Clear signals, if any, to ensure clean start.
      self.signal_handler.consume()
  
  def reset_env(self):
    os.environ.clear()
    os.environ.update(self._environ)
  
  def dup_proc_is_running(self):
    self.signal_handler.emit(SIG_PULSE)
    time.sleep(1.1)
    if SIG_PULSE not in self.signal_handler.peek():
      print(self.signal_handler.peek())
      return True
    else:
      return False
  
  def load_proc_file(self, proc_file, restart=False):
    if not proc_file or not os.path.isfile(proc_file):
      return False
    
    self.register = self.serde_obj.deserialize(proc_file, restart)
    
    if not self.register or not isinstance(self.register, NodeRegister):
      return False
    
    return True
  
  @property
  def notification(self):
    return self._notification
  @notification.setter
  def notification(self, o):
    if not issubclass(type(o), Notification):
      raise TypeError('Not an extension of pyrunner.notification.Notification')
    self._notification = o
    return self
  
  @property
  def version(self):
    return __version__
  @property
  def log_dir(self):
    return self.config['log_dir']
  
  @property
  def config_file(self):
    return self.config['config_file']
  @config_file.setter
  def config_file(self, value):
    self.config['config_file'] = value
    return self
  
  @property
  def proc_file(self):
    return self.config['proc_file']
  @proc_file.setter
  def proc_file(self, value):
    self.config['proc_file'] = value
    return self
  
  @property
  def context(self):
    return self.engine.context
  
  @property
  def restart(self):
    return self.config['restart']
  
  def plugin_serde(self, obj):
    if not isinstance(obj, serde.SerDe): raise Exception('SerDe plugin must implement the SerDe interface')
    self.serde_obj = obj
  
  def plugin_notification(self, obj):
    if not isinstance(obj, notification.Notification): raise Exception('Notification plugin must implement the Notification interface')
    self.notification = obj
  
  # Engine wiring
  def on_create(self, func) : self.engine.on_create(func)
  def on_start(self, func)  : self.engine.on_start(func)
  def on_restart(self, func): self.engine.on_restart(func)
  def on_success(self, func): self.engine.on_success(func)
  def on_fail(self, func)   : self.engine.on_fail(func)
  def on_destroy(self, func): self.engine.on_destroy(func)
  
  # NodeRegister wiring
  def add_node(self, **kwargs)    : return self.register.add_node(**kwargs)
  def exec_only(self, id_list)    : return self.register.exec_only(id_list)
  def exec_to(self, id)           : return self.register.exec_to(id)
  def exec_from(self, id)         : return self.register.exec_from(id)
  def exec_disable(self, id_list) : return self.register.exec_disable(id_list)
  
  def prepare(self):
    # Initialize NodeRegister
    if self.config['restart']:
      self.load_state()
    elif self.config['proc_file']:
      self.load_proc_file(self.config['proc_file'])
    
    # Inject Context var overrides
    for k,v in self.config['cvar_list']:
      self.engine.context.set(k, v)
    
    # Modify NodeRegister
    if self.config['exec_proc_name']:
      self.exec_only([self.register.find_node(name=self.config['exec_proc_name']).id])
    if self.config['exec_only_list']:
      self.exec_only(self.config['exec_only_list'])
    if self.config['exec_disable_list']:
      self.exec_disable(self.config['exec_disable_list'])
    if self.config['exec_from_id'] is not None:
      self.exec_from(self.config['exec_from_id'])
    if self.config['exec_to_id'] is not None:
      self.exec_to(self.config['exec_to_id'])
  
  def execute(self):
    return self.run()
  def run(self):
    self.prepare()
    
    self.config['app_start_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Prepare engine
    self.engine.config = self.config
    self.engine.register = self.register
    self.engine.save_state_func = self.save_state
    
    # Short circuit for a dryrun
    if self.config['dryrun']:
      self.print_documentation()
      return 0
    
    # Fire up engine
    print('Executing PyRunner App: {}'.format(self.config['app_name']))
    retcode = self.engine.initiate()
    
    emit_notification = True
    
    if retcode == 0:
      if not self.config['email_on_success']:
        print('Skipping Email Notification: Property "email_on_success" is set to FALSE.')
        emit_notification = False
    elif retcode > 0:
      if not self.config['email_on_fail']:
        print('Skipping Email Notification: Property "email_on_fail" is set to FALSE.')
        emit_notification = False
    
    if emit_notification:
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
      
      if exit_status == -1:
        suffix = 'ABORT'
      elif exit_status > 0:
        suffix = 'FAILURE'
      else:
        suffix = 'SUCCESS'
      
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
  
  def save_state(self, suppress_output=False, only_ctllog=False):
    if not suppress_output:
      print('Saving Execution Graph File to: {}'.format(self.config.ctllog_file))
    
    self.serde_obj.save_to_file(self.config.ctllog_file, self.register)
    if only_ctllog: return
    
    try:
      
      state_obj = {
        'config'       : self.config.items(),
        'shared_dict'  : self.engine._shared_dict.copy()
      }
      
      if not suppress_output:
        print('Saving Context Object to File: {}'.format(self.config.ctx_file))
      tmp  = self.config.ctx_file+'.tmp'
      perm = self.config.ctx_file
      pickle.dump(state_obj, open(tmp, 'wb'))
      if os.path.isfile(perm):
        os.unlink(perm)
      os.rename(tmp, perm)
      
    except Exception:
      print("Failure in save_context()")
      raise
    
    return
  
  def load_state(self):
    if not self.load_proc_file(self.config.ctllog_file, True):
      return False
    
    if not os.path.isfile(self.config.ctx_file):
      return False
    
    print('Loading prior Context from {}'.format(self.config.ctx_file))
    state_obj = pickle.load(open(self.config.ctx_file, 'rb'))
    
    for k,v in state_obj['config'].items():
      self.config[k] = v
    
    for k,v in state_obj['shared_dict'].items():
      self.engine._shared_dict[k] = v
    
    return True
  
  def delete_state(self):
    if os.path.isfile(self.config.ctllog_file):
      os.remove(self.config.ctllog_file)
    if os.path.isfile(self.config.ctx_file):
      os.remove(self.config.ctx_file)
  
  def is_restartable(self):
    if not os.path.isfile(self.config.ctllog_file):
      return False
    if not os.path.isfile(self.config.ctx_file):
      return False
    return True
  
  def parse_args(self, run_getopts=True):
    abort = False
    
    opt_list = 'c:l:n:e:x:N:D:A:t:drhiv'
    longopt_list = [
      'setup', 'help', 'nozip', 'interactive', 'abort',
      'restart', 'version', 'dryrun', 'debug', 'silent',
      'preserve-context', 'dump-logs', 'allow-duplicate-jobs',
      'email=', 'email-on-fail=', 'email-on-success=',
      'env=', 'cvar=', 'context=', 'time-between-tasks=',
      'to=', 'from=', 'descendants=', 'ancestors=',
      'norun=', 'exec-only=', 'exec-proc-name=',
      'max-procs=', 'serde=', 'exec-loop-interval='
    ]
    
    if run_getopts:
      try:
        opts, _ = getopt.getopt(sys.argv[1:], opt_list, longopt_list)
      except getopt.GetoptError as e:
        print(str(e))
        self.show_help()
        sys.exit(1)
      
      for opt, arg in opts:
        if opt == '-c':
          self.config['config_file'] = arg
        elif opt == '-l':
          self.config['proc_file'] = arg
        elif opt in ['-d', '--debug']:
          self.config['debug'] = True
        elif opt in ['-n', '--max-procs']:
          self.config['max_procs'] = int(arg)
        elif opt in ['-r', '--restart']:
          self.config['restart'] = True
        elif opt in ['-x', '--exec-only']:
          self.config['exec_only_list'] = [ int(id) for id in arg.split(',') ]
        elif opt in ['-N', '--norun']:
          self.config['exec_disable_list'] = [ int(id) for id in arg.split(',') ]
        elif opt in ['-D', '--from', '--descendents']:
          self.config['exec_from_id'] = int(arg)
        elif opt in ['-A', '--to', '--ancestors']:
          self.config['exec_to_id'] = int(arg)
        elif opt in ['-e', '--email']:
          self.config['email'] = arg
        elif opt in ['--email-on-fail']:
          self.config['email_on_fail'] = arg
        elif opt in ['--email-on-success']:
          self.config['email_on_success'] = arg
        elif opt == '--env':
          parts = arg.split('=')
          os.environ[parts[0]] = parts[1]
        elif opt == '--cvar':
          parts = arg.split('=')
          self.config['cvar_list'].append((parts[0], parts[1]))
        elif opt == '--nozip':
          self.config['nozip'] = True
        elif opt == '--dump-logs':
          self.config['dump_logs'] = True
        elif opt == '--dryrun':
          self.config['dryrun'] = True
        elif opt in ['-i', '--interactive']:
          self.engine.context.interactive = True
        elif opt in ['-t', '--tickrate']:
          self.config['tickrate'] = int(arg)
        elif opt in ['--time-between-tasks']:
          self.config['time_between_tasks'] = int(arg)
        elif opt in ['--preserve-context']:
          self.preserve_context = True
        elif opt in ['--allow-duplicate-jobs']:
          self.config['allow_duplicate_jobs'] = True
        elif opt in ['--exec-proc-name']:
          self.config['exec_proc_name'] = arg
        elif opt == '--abort':
          abort = True
        elif opt == '--silent':
          self.config['silent'] = True
        elif opt in ['--serde']:
          if arg.lower() == 'json':
            self.plugin_serde(serde.JsonSerDe())
        elif opt == '--setup':
          pass
        elif opt in ('-h', '--help'):
          self.show_help()
          sys.exit(0)
        elif opt in ('-v', '--version'):
          print('PyRunner v{}'.format(__version__))
          sys.exit(0)
        else:
          raise ValueError("Error during parsing of opts")
    
    # We need to check for and source the app_profile/config file ASAP,
    # but only after --env vars are processed
    if not self.config['config_file']:
      raise RuntimeError('Config file (app_profile) has not been provided')
    self.config.source_config_file(self.config['config_file'])
    
    if abort:
      print('Submitting ABORT signal to running job for: {}'.format(self.config['app_name']))
      self.signal_handler.emit(SIG_ABORT)
      sys.exit(0)
    
    # Check if restart is possible (ctllog/ctx files exist)
    if self.config['restart'] and not self.is_restartable():
      self.config['restart'] = False
  
  def show_help(self):
    print("Options:")
    print("   -c <path>                                 Path to config file.")
    print("   -l <path>                                 Path to process list filename.")
    print("   -r,  --restart                            Start from last known point-of-failure, if any.")
    print("   -n,  --max_procs <num>                    Maximum number of concurrent processes.")
    print("        --exec-proc-name <proc name>         Execute only a single process/task with the given name.")
    print("   -x,  --exec-only <comma seperated nums>   Comma separated list of process ID's to execute. All other processes will be set to NORUN.")
    print("   -N,  --norun <comma separated nums>       Comma separated list of process ID's to NOT execute (set to NORUN).")
    print("   -D,  --descendents <comma separated nums> Comma separated list of process ID's to execute, along with their descendent processes (child procs and beyond).")
    print("   -A,  --ancestors <comma separated nums>   Comma separated list of process ID's to execute, along with their ancestors processes (parent procs and beyond).")
    print("   -e,  --email <email>                      Email to send job notification email upon completion or failure.")
    print("        --email-on-fail <true|false>         Enable/disable job notification email upon failure.")
    print("        --email-on-success <true|false>      Enable/disable job notification email upon success.")
    print("   -d,  --debug                              Prints list of Pending, Running, Failed, and Defaulted tasks instead of summary counts.")
    print("   -i,  --interactive                        Interactive mode. This will force the execution engine to request user input for each non-existent Context variable.")
    print("        --env <VAR_NAME=var_value>           Provide key/value pair to export to the environment prior to execution. Can provide this option multiple times.")
    print("        --cvar <VAR_NAME=var_value>          Provide key/value pair to initialize the Context object with prior to execution. Can provide this option multiple times.")
    print("        --nozip                              Disable behavior which zips up all log files after job exit.")
    print("        --dump-logs                          Enable behavior which prints all failure logs, if any, to STDOUT after job exit.")
    print("   -t,  --tickrate <num>                     Number of times per second that the executon engine should poll child processes/launch new processes. Default is 1.")
    print("        --time-between-tasks <seconds>       Number of seconds, at minimum, that the execution engine should wait after launching a process before launching another.")
    print("        --serde <serializer/deserializer>    Specify the process list serializer/deserializer. Default is LST.")
    print("        --preserve-context                   Disables behavior which deletes the job's context file after successful job exit.")
    print("        --allow-duplicate-jobs               Enables running more than 1 instance of a unique job (based on APP_NAME).")
    print("        --abort                              Aborts running instance of a job (based on APP_NAME), if any.")
    print("        --setup                              Run the PyRunner basic project setup.")
    print("   -v,  --version                            Print PyRunner version.")
    print("   -h,  --help                               Show help (you're reading it right now).")
    return