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

import inspect, re

def print_context_usage(node):
  print('##################################################')
  print('# Module: {}'.format(node.module))
  print('# Worker: {}'.format(node.worker))
  print('##################################################\n')
  
  src = inspect.getsource(node.worker_class)
  
  set_regex = re.compile(r'self.context.set\(\s*?(.+?)\s*?,\s*?(.+?)\s*?\)')
  get_regex = re.compile(r'self.context.get(?:\(\s*?([^,]+?)\s*?\)|\(\s*?(.+?)\s*?,\s*?(.+?)?\s*?\))')
  
  set_results = set_regex.findall(src)
  get_results = get_regex.findall(src)
  
  if set_results:
    print('Context SET Actions:')
  for match in set_results:
    print('  {} : {}'.format(match[0], match[1]))
  if set_results:
    print('')
  
  processed_get_res = set()
  for match in get_results:
    if match[0]:
      processed_get_res.add('{}'.format(match[0].strip()))
    else:
      processed_get_res.add('{} (Default: {})'.format(match[1].strip(), match[2].strip()))
  
  if processed_get_res:
    print('Context GET Actions:')
  for res in list(processed_get_res):
    print('  {}'.format(res))
  if processed_get_res:
    print('')
  
  if not list(processed_get_res)+set_results:
    print('No Context Access\n')
  
  return