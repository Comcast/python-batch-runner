# Overview
The purpose of this project ("PyRunner" for short) is to provide a lightweight, extensible, and non-opinionated development framework for batch applications.

It is intended to simply provide the scaffolding for a batch application without the weight of an all-inclusive or centralized platform, such that the resulting product is portable and not tied down to a specific scheduling or monitoring solution.

The framework encourages deconstructing the steps of a process down to atomic units of logic, such that application state/progress can be managed as a collection of tasks.

It provides the following with zero or minimal setup required:

* Cross-task data/information sharing
* Parallel execution and configurability of task order/dependencies
* Log management
* Job notifications
* Self-managed restartability from point of failure
* Job and task level lifecycle hooks for optional code execution at various steps (such as in the event of failure or job restart)
* Option to implement custom loggers, notifications, workers, etc.

## Installation
```bash
pip install python-batch-runner
```

## Usage

### New Project Setup
A simple setup function is included and can be run by executing:
```bash
pyrunner --setup
```
This will prompt you for three inputs:

1. Project Name
    * Provide a name for your project/application without any spaces (i.e. MySampleProject). If spaces are included, they will be removed.
2. Project Path
    * Provide the path to create the project directory in. The project name (lowercased) will be appended to this path.
    * If left blank, the path will default to the current working directory.

Upon completion, a new directory at the provided (or default/current) path will be created, along with minimum necessary subdirectory and files.

Please see the [Basic Project Structure](./user_guide/project_structure.md) page for more details.

### How to Execute
The most basic PyRunner command requires only the [app_profile](./user_guide/app_profile.md) and [.lst file](./user_guide/lst_file.md):

```bash
# Basic execution with only app_profile and .lst file
pyrunner -c <app_root_path>/config/app_profile -l <app_root_path>/config/<project_name>.lst

# If args needed
pyrunner -c <app_root_path>/config/app_profile -l <app_root_path>/config/<project_name>.lst -r --env PROGRAM_NAME=MY_SAMPLE_PROGRAM
```

This will instruct PyRunner to source the `app_profile` (this is required to provide PyRunner with required application details, such as log and temp dir path) and then execute the workflow described in the `.lst` file.

The **preferred** method, however, is to use a driver Python program, which unlocks access to the framework's full capabilities.

For your convenience, if the --setup utility was used, the `<app_name>.py` (`my_app.py` in this example) file is created which contains:

```python
#!/usr/bin/env python3

import os, sys
from pyrunner import PyRunner
from pathlib import Path

# Determine absolute path of this file's parent directory at runtime
abs_dir_path = os.path.dirname(os.path.realpath(__file__))

# Store path to default config and .lst file
config_file = '{}/config/app_profile'.format(abs_dir_path)
proc_file = '{}/config/my_app.lst'.format(abs_dir_path)

# Init PyRunner and assign default config and .lst file
app = PyRunner(config_file=config_file, proc_file=proc_file)

if __name__ == '__main__':
  # Initiate job and exit driver with return code
  sys.exit(app.execute())
```

This can then simply be executed as below. Note that this method of execution has access to ALL of the same arguments as the `pyrunner -c ...` form.

```bash
# Basic execution with only app_profile and .lst file
./my_app.py

# If args needed, then simply pass as arguments
./my_app.py -r --env PROGRAM_NAME=MY_SAMPLE_PROGRAM

# We can even use the -c and -l options to override the config/lst file
# specified in the driver.
./my_app.py -c /path/to/other/app_profile -l /path/to/other/alternate.lst
```

### Execution Options
| Option | Argument | Description |
| --- | --- | --- |
| --env | [variable_name]=[variable_value] | Set environment variable - equivalent to export [variable_name]=[variable_value] |
| --cvar | [variable_name]=[variable_value] | Set context variable to be available at the start of job. |
| -r | | Restart flag. Causes PyRunner to check the APP_TEMP_DIR for existing *.ctllog files to restart a job from failure. Fresh run if no *.ctllog file found. |
| -n *or* --max-procs | integer | Sets the absolute maximum number of parallel processes allowed to run concurrently. |
| -x *or* --exec-only | comma separated list of process ID's | Executes only the given process ID(s) from the .lst file. |
| --exec-proc-name | single process name | Similar to --exec-only - Executes only the process ID identified by the given process name. |
| -A *or* --to *or* --ancestors | single process ID | Executes given process ID and all preceding/ancestor processes. |
| -D *or* --from *or* --descendents | single process ID | Executes given process ID and all subsequent/descendent processes. |
| -N *or* --norun | comma separated list of process ID's | Prevents the given process ID(s) from executing. |
| -e *or* --email | email address | Sets email address to send job notification email after run completion. Overrides **all** other APP_EMAIL settings. |
| --es *or* --email-on-success | true/false or 1/0 | Enables or disables email notifications when job exits with success. Default is True. |
| --ef *or* --email-on-fail | true/false or 1/0 | Enables or disables email notifications when job exits with failure. Default is True. |
| -i *or* --interactive | | Primarily for use with -x option. Launches in interactive mode which will request input from user if a Context variable is not found. |
| -d *or* --debug | | Debug option that only serves to provide a more detailed output during execution to show names of pending, running, failed, etc. tasks. |
| --dump-logs | | Enables job to dump to STDOUT logs for all failed tasks after job exits. |
| --nozip | | Disables zipping of log files after job exits. |
| -t *or* --tickrate | | Sets the number of checks per second that the execution engine performs to poll running processes. |
| -h *or* --help | | Prints out options and other details. |
| -v *or* --version | | Prints out the installed PyRunner version. |