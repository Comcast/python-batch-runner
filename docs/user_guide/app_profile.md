First of two minimally required files if executing in [Driverless mode](./driverless.md). In [Driver mode](./driver.md) this file may be omitted, however, it is usually convenient and beneficial to have an explicit application profile.

This file serves a similar purpose as the .profile/.bash_profile/.zprofile, but at the application instance level.

The `app_profile` is sourced at the start of every job/batch application instance. In other words, it exports all required environment variables at the very start of execution.

```bash
#!/bin/bash

# This app_profile will be sourced prior to execution of PyRunner job.
# NOTE: Only variables with "APP_" prefix will be available during job.
#       All other variables will be discarded.

export APP_VERSION=0.0.1

export APP_NAME="sample_project"
export APP_ROOT_DIR="$(cd $(dirname ${BASH_SOURCE})/..; pwd)"
export APP_CONFIG_DIR="${APP_ROOT_DIR}/config"
export APP_TEMP_DIR="${APP_ROOT_DIR}/temp"
export APP_ROOT_LOG_DIR="${APP_ROOT_DIR}/logs"
export APP_LOG_RETENTION="30"
export APP_WORKER_DIR="${APP_ROOT_DIR}/workers"

DATE=$(date +"%Y-%m-%d")
export APP_EXEC_TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

export APP_LOG_DIR="${APP_ROOT_LOG_DIR}/${DATE}"

if [ ! -e ${APP_LOG_DIR}  ]; then mkdir -p ${APP_LOG_DIR}; fi
if [ ! -e ${APP_TEMP_DIR} ]; then mkdir ${APP_TEMP_DIR}; fi
```

Syntax is basic SHELL syntax.

Note that only variables that are prefixed with 'APP_' will be accessible during execution after the `app_profile` is sourced. All other variables will be lost.