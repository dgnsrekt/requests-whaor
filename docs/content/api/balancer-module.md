> This module provides objects for managing the network balancer.

<a name="balancer.HAProxyOptions"></a>
## `HAProxyOptions`

> Handles options for HAProxy docker instance.
> 
> **Attributes**:
> 
> - `max_connections` _int_ - Maximum per-process number of concurrent connections.
> - `timeout_client` _int_ - Maximum inactivity time on the client side.
> - `timeout_connect` _int_ - Maximum time to wait for a connection attempt to a server
>   to succeed.
> - `timeout_queue` _int_ - Maximum time to wait in the queue for a connection slot
>   to be free.
> - `timeout_server` _int_ - Maximum inactivity time on the server side.
> - `listen_host_port` _int_ - Frontend port to the proxy.
> - `backend_name` _str_ - Name of Backend section.
> - `dashboard_bind_port` _int_ - Port to open to reach the HAProxy dashboard.
> - `dashboard_refresh_rate` _int_ - Refresh rate of the HAProxy dashboard page.
> - `onions` _List[Container]_ - Each onion container that is connected to the whaornet.

<a name="balancer.HAProxyOptions.Config"></a>
## `Config`

> Pydantic Configuration.

<a name="balancer.HAProxyOptions.ports"></a>
#### `ports`

```python
 | def ports() -> List[int]
```

> Ports which will be used to expose on the local network.

<a name="balancer.Balancer"></a>
## `Balancer`

> HAProxy Load Balancer.
> 
> **Attributes**:
> 
> - `haproxy_options` _HAProxyOptions_ - HAProxy options object.
> - `container_options` _ContainerOptions_ - Container options for the HA proxy instance.

<a name="balancer.Balancer.Config"></a>
## `Config`

> Pydantic Configuration.

<a name="balancer.Balancer.address"></a>
#### `address`

```python
 | def address() -> str
```

> Return socks5 address to poxy requests through.

<a name="balancer.Balancer.dashboard_address"></a>
#### `dashboard_address`

```python
 | def dashboard_address() -> str
```

> Return full dashboard address.

<a name="balancer.Balancer.proxies"></a>
#### `proxies`

```python
 | def proxies() -> Dict[str, str]
```

> Return proxies to mount onto a requests session.

<a name="balancer.Balancer.add_mount_point"></a>
#### `add_mount_point`

```python
 | def add_mount_point(mount: MountFile) -> None
```

> Mount a volume into the HAProxy container.
> 
> **Arguments**:
> 
> - `mount` _MountFile_ - File to mount between the container and local file system.

<a name="balancer.Balancer.display_settings"></a>
#### `display_settings`

```python
 | def display_settings() -> None
```

> Log config settings to stdout.

<a name="balancer.OnionBalancer"></a>
#### `OnionBalancer`

```python
def OnionBalancer(onions: List[OnionCircuit], show_log: bool = False) -> Balancer
```

> Context manager which yields a started instance of an HAProxy docker container.
> 
> **Arguments**:
> 
> - `onions` _List[OnionCircuit]_ - List of tor containers to load balance requests across.
> - `show_log` _bool_ - If True shows the HAProxies logs on start and stop.
>   
> 
> **Yields**:
> 
> - `Balancer` - A started instance of a HAProxy docker container.

