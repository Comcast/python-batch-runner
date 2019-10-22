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
import sys
import getopt
import traceback

import pyrunner.core.constants as constants
import pyrunner.serde as serde
from pyrunner.core.pyrunner import PyRunner
from pyrunner.repomanager import RepoManager


def main():
  pyrunner = PyRunner()
  
  opt_list = 'c:l:n:e:x:N:D:A:t:drhiv'
  longopt_list = [
    'setup',
    'help',
    'nozip',
    'interactive',
    'debug',
    'restart',
    'version',
    'email=',
    'email-on-fail=',
    'email-on-success=',
    'ef=',
    'es=',
    'env=',
    'cvar=',
    'context=',
    'max-procs=',
    'to=',
    'from=',
    'descendants=',
    'ancestors=',
    'norun=',
    'exec-only=',
    'exec-loop-interval=',
    'preserve-context',
    'exec-proc-name=',
    'dump-logs',
    'disable-exclusive-jobs',
    'dryrun',
    'serde='
  ]
  
  try:
    opts, args = getopt.getopt(sys.argv[1:], opt_list, longopt_list)
  except getopt.GetoptError:
    show_help()
    sys.exit(1)
  
  config_file = None
  proc_file   = None
  restart     = False
  env_vars    = {}
  exec_only_list = None
  exec_disable_list = None
  exec_from_id = None
  exec_to_id = None
  exec_proc_name = None
  
  try:
    
    for opt, arg in opts:
      if opt == '-c':
        config_file = arg
      elif opt == '-l':
        proc_file = arg
      elif opt in ['-d', '--debug']:
        pyrunner.config['debug'] = True
      elif opt in ['-n', '--max-procs']:
        pyrunner.config['max_procs'] = int(arg)
      elif opt in ['-r', '--restart']:
        restart = True
      elif opt in ['-x', '--exec-only']:
        exec_only_list = [ int(id) for id in arg.split(',') ]
      elif opt in ['-N', '--norun']:
        exec_disable_list = [ int(id) for id in arg.split(',') ]
      elif opt in ['-D', '--from', '--descendents']:
        exec_from_id = int(arg)
      elif opt in ['-A', '--to', '--ancestors']:
        exec_to_id = int(arg)
      elif opt in ['-e', '--email']:
        pyrunner.config['email'] = arg
      elif opt in ['--ef', '--email-on-fail']:
        pyrunner.config['email_on_fail'] = arg
      elif opt in ['--es', '--email-on-success']:
        pyrunner.config['email_on_success'] = arg
      elif opt == '--env':
        parts = arg.split('=')
        env_vars[parts[0]] = parts[1]
      elif opt == '--cvar':
        parts = arg.split('=')
        pyrunner.context.set(parts[0], parts[1])
      elif opt == '--nozip':
        pyrunner.config['nozip'] = True
      elif opt == '--dump-logs':
        pyrunner.config['dump_logs'] = True
      #elif opt == '--context':
      #  ctx_file = arg
      elif opt == '--dryrun':
        pyrunner.config['dryrun'] = True
      elif opt in ['-i', '--interactive']:
        pyrunner.context.interactive = True
      elif opt in ['-t', '--tickrate']:
        pyrunner.config['tickrate'] = int(arg)
      elif opt in ['--preserve-context']:
        pyrunner.preserve_context = True
      elif opt in ['--disable-exclusive-jobs']:
        pyrunner.disable_exclusive_jobs = True
      elif opt in ['--exec-proc-name']:
        exec_proc_name = arg
      elif opt in ['--serde']:
        if arg.lower() == 'json':
          pyrunner.plugin_serde(serde.JsonSerDe())
      elif opt == '--setup':
        setup()
        sys.exit(0)
      elif opt in ('-h', '--help'):
        show_help()
        sys.exit(0)
      elif opt in ('-v', '--version'):
        print('PyRunner v{}'.format(pyrunner.version))
        sys.exit(0)
      else:
        raise ValueError("Error during parsing of opts")
    
    # Export Command Line Vars to Environment
    for v in env_vars:
      os.environ[v] = env_vars[v]
    
    pyrunner.source_config_file(config_file)
    
    if restart:
      if not pyrunner.load_last_failed():
        pyrunner.load_proc_list_file(proc_file)
    else:
      pyrunner.load_proc_list_file(proc_file)
    
    if exec_proc_name:
      pyrunner.exec_only([pyrunner.register.find_node(name=exec_proc_name).id])
    if exec_only_list:
      pyrunner.exec_only(exec_only_list)
    if exec_disable_list:
      pyrunner.exec_disable(exec_disable_list)
    if exec_from_id is not None:
      pyrunner.exec_from(exec_from_id)
    if exec_to_id is not None:
      pyrunner.exec_to(exec_to_id)
    
    exit_status = pyrunner.execute()
  
  except ValueError as value_error:
    error_code = 2
    print(str(value_error))
    print(traceback.format_exc())
    print('Exiting with code {}'.format(error_code))
    sys.exit(error_code)
  
  except LookupError as file_error:
    error_code = 3
    print(str(file_error))
    print(traceback.format_exc())
    print('Exiting with code {}'.format(error_code))
    sys.exit(error_code)
  
  except KeyboardInterrupt:
    error_code = 4
    print('\nAborting')
    sys.exit(error_code)
  
  except RuntimeError as runtime_error:
    error_code = 5
    print(str(runtime_error))
    print(traceback.format_exc())
    print('Exiting with code {}'.format(error_code))
    sys.exit(error_code)
  
  except OSError as os_error:
    error_code = 6
    print(str(os_error))
    print(traceback.format_exc())
    print('Exiting with code {}'.format(error_code))
    sys.exit(error_code)
  
  except Exception as generic_error:
    error_code = 99
    print('Unknown Exception')
    print(str(generic_error))
    print(traceback.format_exc())
    print('Exiting with code {}'.format(error_code))
    sys.exit(error_code)
  
  sys.exit(exit_status)

# ########################## SHOW HELP ########################## #

def show_help():
  print("Required:")
  print("   -c [CFG_FILENAME] : Provide full path to config file.")
  print("   -l [LST_FILENAME] : Provide full path to process list filename.")
  print("")
  print("Options:")
  print("   -r                     : Use this instead of -l option to execute from last point of failure.")
  print("   -n                     : Maximum number of concurrent processes (Default 10).")
  print("   -x                     : Comma separated list of processes ID's to execute. All other processes will be set to NORUN")
  print("   -h  --help             : Show help (you're reading it right now).")
  print("   -e  --email            : Email to send job notification email upon completion or failure.")
  print("   -ef --email-on-fail    : Email to send job notification email upon failure.")
  print("   -es --email-on-success : Email to send job notification email upon completion.")
  print("   -d  --debug            : Prints list of Pending, Running, Failed, and Defaulted tasks instead of summary counts.")
  print("   -i  --interactive      : Interactive mode. This will force the execution engine to request user input for each non-existent Context variable.")
  print("       --env              : Allows user to provide key/value pair to export to the environment prior to execution. Can provide this option multiple times.")
  print("       --cvar             : Allows user to provide key/value pair to initialize the Context object with prior to execution. Can provide this option multiple times.")
  return

# ########################## SETUP ########################## #

def setup():
  print('\nINITIATING NEW PROJECT SETUP\n')
  app_name = input('Project Name (spaces will be removed): ')
  app_name = app_name.replace(' ', '')
  
  if not app_name.strip():
    raise ValueError('Please provide project name')
  
  app_path = input('Directory to Add Project (Leave Blank for Current Directory): ')
  
  if not app_path.strip():
    app_path = os.getcwd()
  elif not os.path.exists(app_path):
    raise OSError('Provided directory does not exist: {}'.format(app_path))
  elif len(app_path) > 1 and app_path[-1] == '/':
    app_path = app_path[:-1]
  
  app_root = '{}/{}'.format(app_path, app_name.lower())
  
  if os.path.isdir(app_root) or os.path.exists(app_root):
    raise OSError('{} already exists!'.format(app_root))
  
  app_mode = ''
  while app_mode not in [ 'SHELL', 'PYTHON' ]:
    app_mode = input('Setup Project for Which Execution Mode?\nPlease Enter SHELL or PYTHON: ').upper().strip()
    if app_mode not in [ 'SHELL', 'PYTHON' ]:
      print('Invalid Input')
  
  print('\nSUMMARY:\n')
  print('Project Name: {}'.format(app_name.lower()))
  print('Project Path: {}/{}'.format(app_path, app_name.lower()))
  print('Execution Mode: {}'.format(app_mode))
  
  input('\nPress ENTER if this is correct or Ctrl + C to Abort...\n')
  
  print('Proceeding with Project Setup\n')
  
  print('Creating Directory: {}'.format(app_root))
  print('Creating Directory: {}/config'.format(app_root))
  print('Creating Directory: {}/logs'.format(app_root))
  print('Creating Directory: {}/data'.format(app_root))
  print('Creating Directory: {}/temp'.format(app_root))
  if app_mode == 'SHELL': print('Creating Directory: {}/scripts'.format(app_root))
  if app_mode == 'PYTHON': print('Creating Directory: {}/python'.format(app_root))
  
  os.makedirs(app_root)
  os.makedirs('{}/config'.format(app_root))
  if app_mode == 'SHELL': os.makedirs('{}/scripts'.format(app_root))
  if app_mode == 'PYTHON': os.makedirs('{}/python'.format(app_root))
  
  print('Creating Application Profile: {}/config/app_profile'.format(app_root))
  with open('{}/config/app_profile'.format(app_root), 'w') as app_profile:
    app_profile.write('#!/bin/bash\n\n')
    app_profile.write('# This app_profile will be sourced prior to execution of PyRunner job.\n')
    app_profile.write('# NOTE: Only variables with "APP_" prefix will be available during job.\n')
    app_profile.write('#       All other variables will be discarded.\n\n')
    app_profile.write('export APP_NAME="{}"\n'.format(app_name))
    app_profile.write('export APP_ROOT_DIR="$(cd $(dirname ${BASH_SOURCE})/..; pwd)"\n')
    app_profile.write('export APP_CONFIG_DIR="${APP_ROOT_DIR}/config"\n')
    app_profile.write('export APP_TEMP_DIR="${APP_ROOT_DIR}/.temp"\n')
    app_profile.write('export APP_DATA_DIR="${APP_ROOT_DIR}/data"\n')
    app_profile.write('export APP_ROOT_LOG_DIR="${APP_ROOT_DIR}/logs"\n')
    app_profile.write('export APP_LOG_RETENTION="30"\n')
    if app_mode == 'SHELL': app_profile.write('export APP_SCRIPTS_DIR="${APP_ROOT_DIR}/scripts"\n')
    if app_mode == 'PYTHON': app_profile.write('export APP_WORKER_DIR="${APP_ROOT_DIR}/python"\n\n')
    app_profile.write('DATE=$(date +"%Y-%m-%d")\n')
    app_profile.write('export APP_EXEC_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")\n\n')
    app_profile.write('export APP_LOG_DIR="${APP_ROOT_LOG_DIR}/${DATE}"\n\n')
    app_profile.write('if [ ! -e ${APP_LOG_DIR}  ]; then mkdir -p ${APP_LOG_DIR}; fi\n')
    app_profile.write('if [ ! -e ${APP_TEMP_DIR} ]; then mkdir ${APP_TEMP_DIR}; fi\n')
    app_profile.write('if [ ! -e ${APP_DATA_DIR} ]; then mkdir ${APP_DATA_DIR}; fi\n')
  
  print('Creating Blank Process List File: {}/config/{}.lst'.format(app_root, app_name.lower()))
  with open('{}/config/{}.lst'.format(app_root, app_name.lower()), 'w') as lst_file:
    if app_mode == 'SHELL': lst_file.write('{}\n\n'.format(constants.HEADER_SHELL))
    if app_mode == 'PYTHON': lst_file.write('{}\n\n'.format(constants.HEADER_PYTHON))
  
  print('Creating Main Execution Script: {}/main.sh'.format(app_root))
  with open('{}/main.sh'.format(app_root), 'w') as main_file:
    main_file.write('#!/bin/sh\n\n')
    main_file.write('pyrunner -c {}/config/app_profile -l {}/config/{}.lst "$@"\n'.format('$(dirname ${0})', '$(dirname ${0})', app_name.lower()))
  
  os.chmod('{}/main.sh'.format(app_root), 0o744)
  
  print('\nComplete!\n')
  
  return


def repo():
  
  action = sys.argv[1]
  
  package_actions = [ 'package-list', 'package-exists', 'package-add', 'package-remove' ]
  module_actions = [ 'module-list', 'module-exists', 'module-add', 'module-remove', 'module-eject' ]
  
  if action not in package_actions + module_actions:
    print('Invalid action')
    sys.exit(99)
  
  try:
    opts, args = getopt.getopt(sys.argv[2:], 'p:m:d:f', [ 'package=', 'module=', 'destination=', 'force' ])
  except getopt.GetoptError:
    sys.exit(1)
  
  package = None
  module = None
  destination = '.'
  force = False
  
  for opt, arg in opts:
    if opt in ['-p', '--package']:
      package = arg
    elif opt in ['-m', '--module']:
      module = arg
    elif opt in ['-f', '--force']:
      force = True
    elif opt in ['-d', '--destination']:
      destination = arg
    else:
      sys.exit(2)
  
  if not package and action != 'package-list':
    print('Package not provided')
    sys.exit(3)
  if action in module_actions and not module and action != 'module-list':
    print('Module not provided')
    sys.exit(4)
  
  mgr = RepoManager(constants.LOCAL_REPO)
  
  if action == 'package-list':
    packages = mgr.get_packages()
    for p in packages:
      print(p)
  elif action == 'package-exists':
    if package in mgr.get_packages():
      print('Package exists')
    else:
      print('Package does not exist')
  elif action == 'package-add':
    if mgr.add_package(package):
      print('Package added successfully')
    else:
      print('Package was not added')
  elif action == 'package-remove':
    if mgr.remove_package(package, force=force):
      print('Package removed successfully')
    else:
      print('Package was not removed')
  elif action == 'module-list':
    modules = mgr.get_modules(package)
    for m in modules:
      print(m)
  elif action == 'module-exists':
    if module in mgr.get_modules(package):
      print('Module exists')
    else:
      print('Module does not exist')
  elif action == 'module-add':
    if mgr.add_module(package, module, force=force):
      print('Module added successfully')
    else:
      print('Module was not added')
  elif action == 'module-remove':
    if mgr.remove_module(package, module):
      print('Module removed successfully')
    else:
      print('Module was not removed')
  elif action == 'module-eject':
    if mgr.eject_module(package, module, '{}/{}'.format(destination, module)):
      print('Module ejected successfully')
    else:
      print('Module was not ejected')
  else:
    print('Unknown action')
    sys.exit(5)
  
  sys.exit(0)