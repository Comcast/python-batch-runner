# Config
Centralized configuration system. The Config class emulates container objects such that key value pairs can be accessed much like the way they are accessed in dictionaries.

```python
In [1]: from pyrunner import PyRunner

In [2]: pr = PyRunner()

In [3]: pr.config['app_name'] = 'MyNewApp'

In [4]: pr.config['app_name']
Out[3]: 'MyNewApp'
```

Config attributes are typed and additionally have multiple values that each may reference.
The value assigned to a given attribute is taken from the first not-None source, checked in the following order:

1. Manually assigned value
2. Environment variable
3. Hard-coded default

```python
In [1]: pr.config['app_name']
Out[1]: 'PyrunnerApp_5aa9a44c-a252-4505-89f9-b2e741bc1262'

In [2]: os.environ['APP_NAME'] = 'MyNewApp'

In [3]: pr.config['app_name']
Out[3]: 'MyNewApp'

In [4]: pr.config['app_name'] = 'HelloWorldApp'
Out[4]: 'HelloWorldApp'

In [5]: del pr.config['app_name']

In [6]: pr.config['app_name']
Out[6]: 'MyNewApp'
```