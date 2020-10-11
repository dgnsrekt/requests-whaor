> This module provides objects for managing TOR docker instances.

<a name="circuit.OnionCircuit"></a>
## `OnionCircuit`

> A TOR Docker Container Object.
> 
> **Attributes**:
> 
> - `container_options` _ContainerOptions_ - Container Options for TOR docker instance.

<a name="circuit.OnionCircuits"></a>
#### `OnionCircuits`

```python
def OnionCircuits(onion_count: int, startup_with_threads: bool = False, max_threads: int = 2, thread_pool_timeout: Optional[int] = None, show_log: bool = False) -> ContextManager[List[OnionCircuit]]
```

> Context manager which yields a list of started TOR containers.
> 
> Takes care of starting and stopping multiple docker container instances of TOR.
> 
> **Arguments**:
> 
> - `onion_count` _int_ - Number of TOR docker container instances to start.
> - `start_with_threads` _bool_ - If True uses threads to start up the containers.
> - `max_threads` _int_ - Max number of threads to use to start up the containers.
> - `thread_pool_timeout` _Optional[int]_ - Timeout for ThreadPoolExecutor.
> - `show_log` _bool_ - If True shows the containers logs.
>   
> 
> **Yields**:
> 
> - `List[OnionCircuit]` - A list of started OnionCircuit objects.

