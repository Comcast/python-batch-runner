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

SIG_ABORT = 'sig.abort'
SIG_PAUSE = 'sig.pause'
SIG_PULSE = 'sig.pulse'

_valid_signals = (SIG_ABORT, SIG_PAUSE, SIG_PULSE)

class SignalHandler:
  
  def __init__(self, config):
    self.config = config
  
  def sig_file(self, sig):
    return '{}/.{}.{}'.format(self.config['temp_dir'], self.config['app_name'], sig)
  
  def emit(self, sig):
    if sig not in _valid_signals: return ValueError('Unknown signal type: {}'.format(sig))
    open(self.sig_file(sig), 'a').close()
  
  def consume(self):
    sig_set = self.peek()
    for sig in sig_set:
      os.remove(self.sig_file(sig))
    return sig_set
  
  def peek(self):
    return set([ s for s in _valid_signals if os.path.exists(self.sig_file(s)) ])