# python-batch-runner
[![Documentation Status](https://readthedocs.org/projects/python-batch-runner/badge/?version=latest)](https://python-batch-runner.readthedocs.io/en/latest/?badge=latest)

For more complete documentation, please see: https://python-batch-runner.readthedocs.io/

python-batch-runner is a microframework to assist with building small to medium scale batch applications without needing to build the scaffolding from scratch.

It provides the following with zero or minimal setup required:
* Basic project directory structure
* Logging and automatic purging of old log files
* Email notification upon job completion, with attached log files in case of failure
* Configurability of task dependencies and parallel execution
* Self-managed restartability from point of failure and state management
* Data sharing across tasks

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
3. Execution Mode
    * PyRunner will operate in either SHELL or PYTHON mode.
    * NOTE: SHELL-only mode will be deprecated in future versions.

Upon completion, a new directory at the provided (or default/current) path will be created, along with minimum necessary subdirectory and files.

### Core Files
Upon above setup, the following three files will be generated:
* .../config/app_profile
  - Contains a list of exports to setup the basic environment prior to execution. This file is sourced before anything else is executed by PyRunner.
* .../config/<project_name>.lst
  - The process list file.
  - Contains header lines: Line 1 for execution mode (SHELL or PYTHON) and line 2 for column names (line 2 is only for user reference and may be deleted).
  - Any subsequent lines must be entered by the user. Each line must be a single task (pipe-separated) that describes the following:
    a. Task ID (must be unique and 1 or higher)
    b. Parent ID's (comma separated list of numbers that describe which tasks must successfully execute before this task will trigger)
    c. Maximum # of Retries (0 will mean the task will never run; 3 will mean the task will retry upon failure until executed a maximum of 3 times)
    d. Task Name
    e. Task Command (only in SHELL Mode - do not include for PYTHON mode)
    f. Task Module (only in PYTHON Mode - do not include for SHELL mode)
    g. Task Worker (only in PYTHON Mode - do not include for SHELL mode)
    h. Task Arguments (only in PYTHON Mode - do not include for SHELL mode)
    e. Absolute Path to Log File
* .../main.sh
  - For convenience. Simply executes pyrunner with the minimally required options. Any arguments to this script will be passed through to the python script.
  - Not Required

### Execution Modes
#### SHELL Mode
* Will allow any shell command to be executed as a task/process.
* This provides a free-form mode which can allow you to use scripts and executables from any language.
* Executes each task as a new subprocess which inherits from the parent environment, but independent of other task environments.

#### PYTHON Mode
* Restricts execution to only a single class from a user-defined module per task/process.
* Executes each task as a new thread.
* This has the benefit of allowing tasks to communicate via a common set of key/value pairs using a Context object. This effectively allows for the storing of state information during execution, and in case of a failure, this state will be preserved for job restarts.

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

## Contribute
Please read the CONTRIBUTING file for more details.

## License
python-batch-runner is released under the Apache 2.0 License. Please read the LICENSE file for more details.
