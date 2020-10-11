> This module provides base objects to manage docker containers.

<a name="client.Client"></a>
## `Client`

> A Docker Client.
> 
> Provides the methods to connect to a docker engine.
> 
> **Attributes**:
> 
> - `client` _ClassVar[DockerClient]_ - A shared docker client session.

<a name="client.Client.get_client"></a>
#### `get_client`

```python
 | def get_client(cls) -> DockerClient
```

> Return the docker client.

<a name="client.Client.Config"></a>
## `Config`

> Pydantic Configuration.

<a name="client.ContainerOptions"></a>
## `ContainerOptions`

> Docker Container Options.
> 
> Provides common options needed to start a docker container.
> 
> **Attributes**:
> 
> - `container_timeout` _ClassVar[int]_ - Timeout in seconds to wait for the container
>   to stop before sending a SIGKILL.
> - `image` _Optional[str]_ - Name of docker image.
> - `auto_remove` _bool_ - Enable auto-removal of the container on daemon side when the
>   container’s process exits.
> - `detach` _bool_ - Run container in the background and return a Container object.
> - `mounts` _List[DockerMount]_ - Specification for mounts to be added to the container.
> - `ports` _Dict[int, int]_ - Ports to bind inside the container.

<a name="client.ContainerBase"></a>
## `ContainerBase`

> Docker Container Base with default options and commonly used methods.
> 
> **Attributes**:
> 
> - `container_options` _ContainerOptions_ - ContainerOptions Object.
> - `container` _Optional[Container]_ - Holds an instance of a initiated docker container.

<a name="client.ContainerBase.container_id"></a>
#### `container_id`

```python
 | def container_id() -> str
```

> Return container instance id.

<a name="client.ContainerBase.container_short_id"></a>
#### `container_short_id`

```python
 | def container_short_id() -> str
```

> Return container instance short id.

<a name="client.ContainerBase.container_name"></a>
#### `container_name`

```python
 | def container_name() -> str
```

> Return container instance name.

<a name="client.ContainerBase.container_timeout"></a>
#### `container_timeout`

```python
 | def container_timeout() -> int
```

> Return container timeout.

<a name="client.ContainerBase.show_follow_logs_command"></a>
#### `show_follow_logs_command`

```python
 | def show_follow_logs_command() -> None
```

> Print log message with docker container logs command.

<a name="client.ContainerBase.expose_port"></a>
#### `expose_port`

```python
 | def expose_port(port: int) -> None
```

> Add ports to expose to the container options.
> 
> **Arguments**:
> 
> - `port` _int_ - The port to expose.

<a name="client.ContainerBase.start"></a>
#### `start`

```python
 | def start(show_log: bool = False) -> None
```

> Start a container instance.
> 
> **Arguments**:
> 
> - `show_log` _bool_ - If True shows the containers logs.

<a name="client.ContainerBase.restart"></a>
#### `restart`

```python
 | def restart() -> None
```

> Restart the container instance.

<a name="client.ContainerBase.print_logs"></a>
#### `print_logs`

```python
 | def print_logs() -> None
```

> Print the container instance logs.

<a name="client.ContainerBase.stop"></a>
#### `stop`

```python
 | def stop(show_log: bool = False) -> None
```

> Stop a container instance.
> 
> **Arguments**:
> 
> - `show_log` _bool_ - If True shows the containers logs.

