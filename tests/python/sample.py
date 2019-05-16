import time

class SayHello:
  def run(self):
    self.logger.info('Hello World!')
    return

class FailMe:
  def run(self):
    return 1