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

from pyrunner.worker.abstract import Worker
from subprocess import run, Popen, PIPE, STDOUT

class ShellWorker(Worker):
  """
  Pre-defined worker for executing raw Shell command given in the Worker
  self.argv property. STDOUT/STDERR is redirected to configured logger.
  """
  
  def run(self):
    command = self.argv
    
    proc = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)
    
    for line in iter(proc.stdout.readline, b''):
      self.logger.info(line.decode('UTF-8'))
    
    proc.communicate()
    return proc.returncode