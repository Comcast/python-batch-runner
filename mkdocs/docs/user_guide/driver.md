Driver mode provides the option to implement a more dynamic batch process.

While the `app_profile` and `.lst` files may still be used in this mode, they are no longer strictly required.

In the custom driver program, the application's [Config](./config.md) and [ExecutionGraph](./execution_graph.md) must be manually constructed.

Since the ExecutionGraph can now be constructed at runtime, it is no longer restricted to a static `.lst` file and the graph may be shaped based on logic implemented in the driver.