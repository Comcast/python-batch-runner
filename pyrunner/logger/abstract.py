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

from abc import ABCMeta, abstractmethod

class Logger:
  __metaclass__ = ABCMeta
  
  @abstractmethod
  def open(self, open_message=True):
    """
    Open stream for target log object.
    """
    raise NotImplementedError('Method "open" is not implemented')
  
  @abstractmethod
  def info(self, text):
    """
    Write a standard INFO level log message.
    """
    raise NotImplementedError('Method "info" is not implemented')
  
  @abstractmethod
  def success(self, text):
    """
    Write a SUCCESS level log message.
    """
    raise NotImplementedError('Method "success" is not implemented')
  
  @abstractmethod
  def error(self, text):
    """
    Write an ERROR level log message.
    """
    raise NotImplementedError('Method "error" is not implemented')
  
  @abstractmethod
  def restart_message(self, restart_count):
    """
    Write a RESTART attempt indication message.
    """
    raise NotImplementedError('Method "restart" is not implemented')
  
  @abstractmethod
  def close(self):
    """
    Close stream for target log object.
    """
    raise NotImplementedError('Method "close" is not implemented')
  
  @abstractmethod
  def dump_log(self):
    """
    Dump contents of target log object to STDOUT.
    """
    raise NotImplementedError('Method "dump_log" is not implemented')