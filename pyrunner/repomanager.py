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

class RepoManager:
  
  def __init__(self, repo_dir):
    self.repo = repo_dir
    self.packages = []
    
    if not os.path.exists(self.repo):
      os.mkdir(self.repo)
      open('{}/__init__.py'.format(self.repo), 'w').close()
    else:
      self.packages = [ os.path.basename(x[0]) for x in os.walk(self.repo) ][1:]
    
    return
  
  def set_repo(self, repo):
    self.repo = repo
    return
  
  def get_repo(self):
    return self.get_repo()
  
  def get_packages(self):
    return self.packages
  
  def get_modules(self, package):
    modules = []
    
    if not self.package_exists(package):
      return []
    else:
      list_of_lists = [ x[2] for x in os.walk('{}/{}'.format(self.repo, package)) ]
    
    for l in list_of_lists:
      modules.extend(l)
    
    return [ os.path.basename(x) for x in modules ]
  
  def package_exists(self, package):
    return package in self.packages
  
  def module_exists(self, package, module):
    return module in self.get_modules(package)
  
  def add_package(self, package):
    if not self.package_exists(package):
      os.mkdir('{}/{}'.format(self.repo, package))
      return True
    else:
      return False
    return
  
  def remove_package(self, package, force=False):
    force_removal = force
    
    if not self.package_exists(package):
      return False
    
    if self.get_modules(package):
      if not force_removal:
        return False
      else:
        shutil.rmtree('{}/{}'.format(self.repo, package))
        return True
    else:
      os.rmdir('{}/{}'.format(self.repo, package))
      return True
    
    return False
  
  def add_module(self, package, module_path, force=False):
    force_add = force
    module = os.path.basename(module_path)
    
    if not self.package_exists(package):
      return False
    
    if self.module_exists(package, module):
      if not force_add:
        return False
      else:
        os.remove('{}/{}/{}'.format(self.repo, package, module))
    
    shutil.copyfile(module_path, '{}/{}/{}'.format(self.repo, package, module))
    return True
  
  def remove_module(self, package, module):
    if not self.package_exists(package):
      return False
    
    if not self.module_exists(package, module):
      return True
    
    os.remove('{}/{}/{}'.format(self.repo, package, module))
    return True
  
  def eject_module(self, package, module, destination):
    if not self.package_exists(package):
      return False
    
    if not self.module_exists(package, module):
      return False
    
    shutil.copyfile('{}/{}/{}'.format(self.repo, package, module), destination)
    return True