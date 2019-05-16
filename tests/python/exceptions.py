class ThrowValueError:
  def run(self):
    raise ValueError()

class ThrowRuntimeError:
  def run(self):
    raise RuntimeError()

class InvalidInt:
  def run(self):
    int('this cannot be cast to int')