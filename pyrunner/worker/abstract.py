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

import traceback, sys

import pyrunner.logger.file as lg

from abc import ABC, abstractmethod

class Worker(ABC):
  """
  Abstract class from which user-defined workers must be derived.
  
  This is responsible for providing the appropriate lifecycle hooks
  that user-defined workers may implement (only run() is mandatory):
    - run()
    - on_success()
    - on_fail()
    - on_exit()
  """
  
  def __init__(self, context, retcode, logfile, argv):
    self.context = context
    self._retcode = retcode
    self.logfile = logfile
    self.logger = lg.FileLogger(logfile).open()
    self.argv = argv
    return
  
  # The _retcode is handled by multiprocessing.Manager and requires special handling.
  @property
  def retcode(self):
    return self._retcode.value
  @retcode.setter
  def retcode(self, value):
    if int(value) < 0:
      raise ValueError('retcode must be 0 or greater - received: {}'.format(value))
    self._retcode.value = int(value)
    return self
  
  def protected_run(self):
    """
    Initiate worker class run method and additionally trigger other lifecycle
    methods, if defined.
    """
    
    if self.logfile:
      sys.stdout = open(self.logfile, 'a')
      sys.stderr = open(self.logfile, 'a')
    
    # RUN
    try:
      self.retcode = self.run() or self.retcode
    except Exception as e:
      self.logger.error("Uncaught Exception from Worker Thread (RUN)")
      self.logger.error(str(e))
      self.logger.error(traceback.format_exc())
      self.retcode = 901
    
    if not self.retcode:
      # ON SUCCESS
      try:
        self.retcode = self.on_success() or self.retcode
      except NotImplementedError:
        pass
      except Exception as e:
        self.logger.error('Uncaught Exception from Worker Thread (ON_SUCCESS)')
        self.logger.error(str(e))
        self.logger.error(traceback.format_exc())
        self.retcode = 902
    else:
      # ON FAIL
      try:
        self.on_fail() or self.retcode
      except NotImplementedError:
        pass
      except Exception as e:
        self.logger.error('Uncaught Exception from Worker Thread (ON_FAIL)')
        self.logger.error(str(e))
        self.logger.error(traceback.format_exc())
        self.retcode = 903
    
    # ON EXIT
    try:
      self.retcode = self.on_exit() or self.retcode
    except NotImplementedError:
        pass
    except Exception as e:
      self.logger.error('Uncaught Exception from Worker Thread (ON_EXIT)')
      self.logger.error(str(e))
      self.logger.error(traceback.format_exc())
      self.retcode = 904
    
    if sys.stdout: sys.stdout.close()
    if sys.stderr: sys.stderr.close()
    self.logger.close()
    
    return
  
  # To be implemented in user-defined workers.
  @abstractmethod
  def run(self):
    """
    Mandatory lifecycle method. The main body of user-defined worker should be
    implemented here.
    """
    pass
  
  def on_success(self):
    """
    Optional lifecycle method. Is only executed if the run() method returns
    without failure (self.retcode == 0)
    """
    raise NotImplementedError('Method "on_success" is not implemented')
  
  def on_fail(self):
    """
    Optional lifecycle method. Is only executed if the run() method returns
    without failure (self.retcode != 0)
    """
    raise NotImplementedError('Method "on_fail" is not implemented')
  
  def on_exit(self):
    """
    Optional lifecycle method. Is always executed, if implemented, but always
    after on_success() or on_fail().
    """
    raise NotImplementedError('Method "on_exit" is not implemented')
  