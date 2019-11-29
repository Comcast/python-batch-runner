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

from datetime import datetime as datetime

STATUS_COMPLETED = 'C'
STATUS_PENDING   = 'P'
STATUS_RUNNING   = 'R'
STATUS_FAILED    = 'F'
STATUS_DEFAULTED = 'D'
STATUS_NORUN     = 'N'
STATUS_ABORTED   = 'A'

EXECUTION_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

MODE_SHELL  = 'SHELL'
MODE_PYTHON = 'PYTHON'

HEADER_SHELL  = '#{}\n#ID|PARENT_IDS|MAX_ATTEMPTS|RETRY_WAIT_TIME|PROCESS_NAME|SHELL_COMMAND|LOGFILE'.format(MODE_SHELL)
HEADER_PYTHON = '#{}\n#ID|PARENT_IDS|MAX_ATTEMPTS|RETRY_WAIT_TIME|PROCESS_NAME|MODULE_NAME|WORKER_NAME|ARGUMENTS|LOGFILE'.format(MODE_PYTHON)

ROOT_NODE_NAME = 'PyRunnerRootNode'

DRIVER_TEMPLATE = """
#!/usr/bin/env python3

import sys
from pyrunner import PyRunner
from pathlib import Path

def main():
  app = PyRunner()
  
  # Assign default config and .lst file
  app.source_config_file(Path('{}/app_profile'.format(app.config['config_dir'])))
  app.load_from_file(Path('{}/{}.lst'.format(app.config['config_dir'], app.config['app_name'])))
  
  # Parse command line args
  app.parse_args()
  
  # Initiate job
  exit_status = app.execute()
  
  # Ensure job exit status is passed to the caller
  sys.exit(exit_status)

if __name__ == '__main__':
  main()
"""