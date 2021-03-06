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

import traceback, sys, time
import multiprocessing.sharedctypes

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
  
  def __init__(self, context, logfile, argv, as_service, service_exec_interval=1):
    self.context = context
    self._retcode = multiprocessing.sharedctypes.Value('i', 0)
    self.logfile = logfile
    self.logger = None
    self.argv = argv
    self._as_service = as_service
    self._service_exec_interval = service_exec_interval
    
    return
  
  def cleanup(self):
    self._retcode = None
  
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
    
    self.logger = lg.FileLogger(self.logfile).open()
    sys.stdout = self.logger.logfile_handle
    sys.stderr = self.logger.logfile_handle
    
    # ON START
    try:
      self.retcode = self.on_start() or self.retcode
    except NotImplementedError:
      pass
    except Exception as e:
      self.logger.error('Uncaught Exception from Worker Thread (ON_START)')
      self.logger.error(str(e))
      self.logger.error(traceback.format_exc())
      self.retcode = 902
    
    # RUN
    try:
      while True:
        self.retcode = self.run() or self.retcode
        if not self._as_service: break
        time.sleep(self._service_exec_interval)
    except Exception as e:
      self.logger.error("Uncaught Exception from Worker Thread (RUN)")
      self.logger.error(str(e))
      self.logger.error(traceback.format_exc())
      self.retcode = 903
    
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
        self.retcode = 904
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
        self.retcode = 905
    
    # ON EXIT
    try:
      self.retcode = self.on_destroy() or self.retcode
    except NotImplementedError:
        pass
    except Exception as e:
      self.logger.error('Uncaught Exception from Worker Thread (ON_DESTROY)')
      self.logger.error(str(e))
      self.logger.error(traceback.format_exc())
      self.retcode = 906
    
    self.logger.close()
    self.logger = None
    
    return
  
  # To be implemented in user-defined workers.
  def on_start(self):
    """
    Optional lifecycle method. Is only executed when the worker is started/restarted.
    This part of the lifecycle is redundant to the run() method unless app is run as a service.
    """
    raise NotImplementedError('Method "on_start" is not implemented')
  
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
  
  def on_destroy(self):
    """
    Optional lifecycle method. Is always executed, if implemented, but always
    after on_success() or on_fail().
    """
    raise NotImplementedError('Method "on_destroy" is not implemented')
  