Each task described in the process list file must be assigned a single Worker class.

In the following line from an example process list:
```
2|1|1|0|Download Delta File|process|DownloadFile||$ENV{APP_LOG_DIR}/download_delta_file.log
```
PyRunner will look within the ${APP_WORKER_DIR} (defined in the [app_profile](./app_profile.md)) for class `DownloadFile` in `process.py`.

The `DownloadFile` class is expected to extend the `pyrunner.Worker` abstract class and implement the `run(self)` method at minimum.

## Worker Properties
Implementations of the Worker class have the following class properties available to them:

* `self.argv` - argument vector to access positional arguments optionally provided in the .lst file.
* `self.logger` - simple logger object with `.info(<message>)` and `.error(<message>)` methods that write provided string to the text file indicated in the .lst file (`$ENV{APP_LOG_DIR}` in the above example).
* `self.context` - a thread-safe key/value store shared across all tasks within a given instance of a job, which provides the ability to share data across separate tasks.

## Worker Lifecycle Methods
Additionally, there exist lifecycle methods (in addition to the mandatory `run(self)` method) that may optionally be implemented:

* `on_success(self)` - only invoked upon successful execution of the `run(self)` method.
* `on_fail(self)` - only invoked upon failed execution of the `run(self)` method.
* `on_exit(self)` - always invoked upon completion of the `run(self)` method.

## Return Codes and Exceptions
Return values are not explicitly required for any lifecycle method - the absence of an explicit return or prematurely returning None/0 will result in ending the task in success.

In the case that the task must be prematurely ended in failure, either a non-zero/not-None value may be returned:
```python
  # Do something
  if my_value == 'something unexpected':
    self.logger.error('my_value is not assigned the appropriate value!')
    return 99
```

or an exception may be raised:
```python
  # Do something
  if my_value == 'something unexpected':
    raise ValueError('my_value is not assigned the appropriate value!')
```

Raising an exception is the preferred method of ending a task in failure.

All exceptions, whether intentionally thrown or unexpectedly encountered, will have the exception message and stack trace written to the log file and return a non-zero return code.