> This module provides core requests_whaor functionality.

<a name="core.pause"></a>
#### `pause`

```python
def pause(sleep: int) -> None
```

> Sleep function with a little logging fun.

<a name="core.Requestor"></a>
## `Requestor`

> Makes proxied web requests via a rotating proxy TOR network.

<a name="core.Requestor.__init__"></a>
#### `__init__`

```python
 | def __init__(onions: List[OnionCircuit], onion_balancer: Balancer, timeout: int, max_retries: int) -> "Requestor"
```

> Requestor __init__ method.
> 
> **Arguments**:
> 
> - `onions` _List[OnionCircuit]_ - List of TOR containers.
> - `onion_balancer` _Balancer_ - Balancer instances connected to TOR containers
>   on the same network.
> - `timeout` _int_ - Requests timeout.
> - `max_retries` _int_ - Max number of time to retry on bad response or connection error.

<a name="core.Requestor.rotating_proxy"></a>
#### `rotating_proxy`

```python
 | def rotating_proxy() -> Dict[str, str]
```

> Rotating proxy frontend input address.

<a name="core.Requestor.get"></a>
#### `get`

```python
 | def get(url: str, *args, **kwargs) -> Optional[requests.models.Response]
```

> Overload requests.get method.
> 
> This will pass in the rotating proxy host address and timeout into the requests.get
> method. Additionally, It provides a way to automatically retry on connection failures
> and bad status_codes. Each time there is a failure it will try a new request with
> a new ip address.
> 
> **Arguments**:
> 
> - `url` _str_ - url to send the get request.
> - `*args` - arguments to pass to requests.get() method.
> - `**kwargs` - keyword arguments to pass to requests.get() method.
>   
> 
> **Returns**:
> 
> - `Response` - If a response is found else None.

<a name="core.Requestor.restart_onions"></a>
#### `restart_onions`

```python
 | def restart_onions(with_threads: bool = True, max_threads: int = 5) -> None
```

> Restart onion containers.
> 
> This can be useful for changing ip addresses every n requests.
> 
> **Arguments**:
> 
> - `with_threads` _bool_ - if True uses threads to restart the containers.
> - `max_threads` _int_ - How many threads to use.

<a name="core.RequestsWhaor"></a>
#### `RequestsWhaor`

```python
def RequestsWhaor(onion_count: int = 5, start_with_threads: bool = True, max_threads: int = 5, timeout: int = 5, show_log: bool = False, max_retries: int = 5) -> Requestor
```

> Context manager which starts n amount of tor nodes behind a round robin reverse proxy.
> 
> **Arguments**:
> 
> - `onion_count` _int_ - Number of TOR circuits to spin up.
> - `start_with_threads` _bool_ - If True uses treads to spin up containers.
> - `max_threads` _int_ - Max number of threads to use when spin up containers.
> - `timeout` _int_ - Requests timeout.
> - `show_log` _bool_ - If True shows the containers logs.
> - `max_retries` _int_ - Max number of time to retry on bad response or connection error.
>   
> 
> **Yields**:
> 
> - `Requestor` - Makes proxied web requests via a rotating proxy TOR network.

