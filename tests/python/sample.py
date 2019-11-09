import time
from pyrunner import Worker

class SayHello(Worker):
  def run(self):
    self.logger.info('Hello World!')
    return

class FailMe(Worker):
  def run(self):
    return 1