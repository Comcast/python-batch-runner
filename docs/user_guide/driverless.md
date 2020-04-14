Driverless mode is the simplest form of a PyRunner application and is suited for batch processes that follow one or few static workflows.

This form is termed "driverless" as it does not require that a custom Python driver program to be written as it's entry point.

Driverless mode requires only the [app_profile](./user_guide/app_profile.md) and [.lst file](./user_guide/lst_file.md) file:

```bash
# Basic execution with only app_profile and .lst file
pyrunner -c <app_root_path>/config/app_profile -l <app_root_path>/config/<project_name>.lst
```