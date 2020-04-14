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
  def _emit_(self, level, text):
    """
    Write log message with given level. This is the method that must be implemented
    at minimum to allow for the logger to understand how to write a message to a
    target log.
    """
    raise NotImplementedError('Method _emit_ is not implemented')
  
  def info(self, text):
    """
    Write a standard INFO level log message.
    """
    self._emit_('INFO', text)
  
  def success(self, text):
    """
    Write a SUCCESS level log message.
    """
    self._emit_('SUCCESS', text)
  
  def warn(self, text):
    """
    Write a standard WARN level log message.
    """
    self._emit_('WARN', text)
  
  def error(self, text):
    """
    Write an ERROR level log message.
    """
    self._emit_('ERROR', text)
  
  def _system_(self, text):
    """
    Write a generic SYSTEM level log message.
    This is reserved for internal control messages.
    """
    self._emit_('SYSTEM', text)
  
  @abstractmethod
  def restart_message(self, restart_count, extra_text):
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