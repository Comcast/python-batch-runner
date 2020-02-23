# Process List File

Second of two minimally required files if executing in [Driverless mode](./driverless.md). In [Driver mode](./driver.md) this file may be omitted, however, it is usually convenient and beneficial to have an explicit process list file.

This is a serialization of the Execution graph (a DAG) and defines all tasks to be executed, as well as their dependencies on each other.

## Sample .lst File
```bash
#PYTHON
#ID|PARENT_IDS|MAX_ATTEMPTS|RETRY_WAIT_TIME|PROCESS_NAME|MODULE_NAME|WORKER_NAME|ARGUMENTS|LOGFILE
1|-1|1|0|Start Job|job|JobStart||$ENV{APP_LOG_DIR}/start_job.log
2|1|1|0|Download Delta File|process|DownloadFile||$ENV{APP_LOG_DIR}/download_delta_file.log
3|1|1|0|Read from Table|process|ReadTable||$ENV{APP_LOG_DIR}/read_table.log
4|2,3|1|0|Write Results File|process|WriteResults||$ENV{APP_LOG_DIR}/write_results.log
5|4|1|0|End Job|job|JobEnd||$ENV{APP_LOG_DIR}/end_job.log
```

Each line contains a single task defined by the following parameters (pipe-separated):

* **Task ID**: must be unique and 1 or higher
* **Parent ID's**: comma separated list of numbers that describe which tasks must successfully execute before this task will trigger
* **Maximum # of Attempts**: 1 will mean no retry upon failure; 3 will mean the task will retry upon failure up to 2 times, until success or executed a maximum of 3 times
* **Retry Wait Time**: number of seconds between retry attempts on failure
* **Task Name**: unique task name for easier identification
* **Task Module**: Python file under the `worker` directory. e.g. for the `process` module, a `<app_root>/worker/process.py` is expected
* **Task Worker**: see [Worker](./worker.md) page for more details
* **Task Arguments**: optional comma-separated positional arguments
* **Path to Log File**: can use `$ENV{APP_LOG_DIR}` to write to log dir specified in the [app_profile](./app_profile.md)

Any environment variables can be referenced using the `$ENV{}` syntax and will be substituted at the start of execution.