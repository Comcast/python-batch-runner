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

MODE_PYTHON = 'PYTHON'
HEADER_PYTHON = '#{}\n#ID|PARENT_IDS|MAX_ATTEMPTS|RETRY_WAIT_TIME|PROCESS_NAME|MODULE_NAME|WORKER_NAME|ARGUMENTS|LOGFILE'.format(MODE_PYTHON)

ROOT_NODE_NAME = 'PyRunnerRootNode'

DRIVER_TEMPLATE = """#!/usr/bin/env python3

import os, sys
from pyrunner import PyRunner

if __name__ == '__main__':
  # Determine absolute path of this file's parent directory at runtime
  abs_dir_path = os.path.dirname(os.path.realpath(__file__))
  
  # Store path to default config and .lst file
  config_file = '{{}}/config/app_profile'.format(abs_dir_path)
  proc_file = '{{}}/config/{app_name}.lst'.format(abs_dir_path)
  
  # Init PyRunner and assign default config and .lst file
  app = PyRunner(config_file=config_file, proc_file=proc_file)
  
  # Initiate job and exit driver with return code
  sys.exit(app.execute())
"""