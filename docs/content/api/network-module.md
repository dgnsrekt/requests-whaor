> This module provides objects for managing docker network instances.

<a name="network.Network"></a>
## `Network`

> Represents a docker network.
> 
> **Attributes**:
> 
> - `name` _str_ - Network name.
> - `driver` _str_ - Network driver.
> - `docker_network` _Optional[DockerNetwork]_ - Holds an instance of a started docker network.

<a name="network.Network.connect_container"></a>
#### `connect_container`

```python
 | def connect_container(container_id: str, container_name: str) -> None
```

> Connect container to network and give it a reachable network alias.
> 
> **Arguments**:
> 
> - `container_id` _str_ - The containers id.
> - `container_name` _str_ - The containers name.

<a name="network.Network.containers"></a>
#### `containers`

```python
 | def containers() -> List[DockerContainer]
```

> Return list of Container objects connected to network.

<a name="network.Network.network_name"></a>
#### `network_name`

```python
 | def network_name() -> str
```

> Network name.

<a name="network.Network.network_id"></a>
#### `network_id`

```python
 | def network_id() -> str
```

> Network short id.

<a name="network.Network.start"></a>
#### `start`

```python
 | def start() -> None
```

> Start Docker network.

<a name="network.Network.stop"></a>
#### `stop`

```python
 | def stop() -> None
```

> Stop Docker network.

<a name="network.WhaorNet"></a>
#### `WhaorNet`

```python
def WhaorNet(name: str = "whaornet", driver: str = "bridge") -> ContextManager[Network]
```

> Context manager which yields a network to connect containers to.
> 
> **Arguments**:
> 
> - `name` _str_ - Name of network.
> - `driver` _str_ - Type of network drivier.
>   
> 
> **Yields**:
> 
> - `Network` - A Docker network.

