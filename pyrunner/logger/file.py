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
import shutil
from datetime import datetime as datetime
from pyrunner.logger.abstract import Logger

class FileLogger(Logger):

  def __init__(self, filename=None):
    self.filename = os.path.abspath(filename) if filename else os.devnull
    self.logfile_handle = None
    return
  
  def open(self, open_message=True):
    """
    Open stream for target log file.
    """
    if not self.logfile_handle:
      try:
        self.logfile_handle = open(self.filename, "a")
        if open_message:
          self.logfile_handle.write("############################################################################\n")
          self.logfile_handle.write("# LOG START - {}\n".format(datetime.now()))
          self.logfile_handle.write("############################################################################\n\n")
          self.logfile_handle.flush()
      except Exception as e:
        print(str(e))
    return self
  
  def _emit_(self, level, text):
    """
    Write log message with given level.
    """
    self.logfile_handle.write("{} - {} - {}\n".format(level.upper(), datetime.now(), text))
    self.logfile_handle.flush()
    return
  
  def restart_message(self, restart_count):
    """
    Write a RESTART attempt indication message.
    """
    self.logfile_handle.write("\n############################################################################\n")
    self.logfile_handle.write("# RESTART ATTEMPT {} - {}\n".format(restart_count, datetime.now()))
    self.logfile_handle.write("############################################################################\n\n")
    self.logfile_handle.flush()
    return
  
  def close(self):
    """
    Close stream for target log file.
    """
    if self.logfile_handle:
      self.logfile_handle.write("\n############################################################################\n")
      self.logfile_handle.write("# LOG END - {}\n".format(datetime.now()))
      self.logfile_handle.write("############################################################################\n\n")
      self.logfile_handle.close()
    return
  
  def get_file_handle(self):
    """
    Return the file handle for target log.
    
    Returns:
      logfile_handle: File handle.
    """
    return self.logfile_handle
  
  def file_is_open(self):
    """
    Check if target log file is currently open for writing.
    
    Returns:
      is_open (bool): True if open/writable, otherwise False.
    """
    return True if self.logfile_handle else False
  
  def dump_log(self):
    """
    Dump contents of target log file to STDOUT.
    """
    with open(self.filename, 'r') as f:
      for line in f:
        print(line, end='')
    return