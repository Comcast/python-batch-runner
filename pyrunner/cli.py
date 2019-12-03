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

def main():
  exit_status = 0
  
  if '--setup' in sys.argv:
    setup()
  else:
    try:
      app = PyRunner()
      exit_status = app.execute()
    except ValueError as value_error:
      exit_status = 2
      print(str(value_error))
      print(traceback.format_exc())
      print('Exiting with code {}'.format(exit_status))
    
    except LookupError as file_error:
      exit_status = 3
      print(str(file_error))
      print(traceback.format_exc())
      print('Exiting with code {}'.format(exit_status))
    
    except KeyboardInterrupt:
      exit_status = 4
      print('\nAborting')
    
    except RuntimeError as runtime_error:
      exit_status = 5
      print(str(runtime_error))
      print(traceback.format_exc())
      print('Exiting with code {}'.format(exit_status))
    
    except OSError as os_error:
      exit_status = 6
      print(str(os_error))
      print(traceback.format_exc())
      print('Exiting with code {}'.format(exit_status))
    
    except Exception as generic_error:
      exit_status = 99
      print('Unknown Exception')
      print(str(generic_error))
      print(traceback.format_exc())
      print('Exiting with code {}'.format(exit_status))
  
  sys.exit(exit_status)

# ########################## SETUP ########################## #

def setup():
  print('\nINITIATING NEW PROJECT SETUP\n')
  app_name = input('Project Name (spaces will be removed): ')
  app_name = app_name.replace(' ', '_').lower()
  
  if not app_name.strip():
    raise ValueError('Please provide project name')
  
  app_path = input('Directory to Add Project (Leave Blank for Current Directory): ')
  
  if not app_path.strip():
    app_path = os.getcwd()
  elif not os.path.exists(app_path):
    raise OSError('Provided directory does not exist: {}'.format(app_path))
  elif len(app_path) > 1 and app_path[-1] == '/':
    app_path = app_path[:-1]
  
  app_root = '{}/{}'.format(app_path, app_name)
  
  if os.path.isdir(app_root) or os.path.exists(app_root):
    raise OSError('{} already exists!'.format(app_root))
  
  app_mode = ''
  while app_mode not in [ 'SHELL', 'PYTHON' ]:
    app_mode = input('Setup Project for Which Execution Mode?\nPlease Enter SHELL or PYTHON: ').upper().strip()
    if app_mode not in [ 'SHELL', 'PYTHON' ]:
      print('Invalid Input')
  
  print('\nSUMMARY:\n')
  print('Project Name: {}'.format(app_name))
  print('Project Path: {}/{}'.format(app_path, app_name))
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
  
  print('Creating Blank Process List File: {}/config/{}.lst'.format(app_root, app_name))
  with open('{}/config/{}.lst'.format(app_root, app_name), 'w') as lst_file:
    if app_mode == 'SHELL': lst_file.write('{}\n\n'.format(constants.HEADER_SHELL))
    if app_mode == 'PYTHON': lst_file.write('{}\n\n'.format(constants.HEADER_PYTHON))
  
  print('Creating Driver Program: {}/{}.py'.format(app_root, app_name))
  with open('{}/{}.py'.format(app_root, app_name), 'w') as main_file:
    main_file.write(constants.DRIVER_TEMPLATE.format(app_name=app_name))
  
  os.chmod('{}/{}.py'.format(app_root, app_name), 0o744)
  
  print('\nComplete!\n')
  
  return