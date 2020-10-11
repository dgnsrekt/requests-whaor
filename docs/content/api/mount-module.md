> This module provides objects for managing docker mount instances.

<a name="mount.MountFile"></a>
## `MountFile`

> Represents a file to be binded to a docker container.
> 
> **Attributes**:
> 
> - `template_name` _str_ - Name of the jinja template.
> - `target_path` _str_ - Local file system path.
> - `volume_driver` _str_ - Type of docker volume.
> - `temporary_file` _Optional[TemporaryFile]_ - A mounted instance of a TemporaryFile.
> - `mount` _Optional[Mount]_ - An instance of the DockerMount.
> - `template_variables` _Optional[Dict[Any, Any]]_ - Jinja template variables.

<a name="mount.MountFile.Config"></a>
## `Config`

> Pydantic Configuration.

<a name="mount.MountFile.volume_name"></a>
#### `volume_name`

```python
 | def volume_name() -> str
```

> Name of the volume.

<a name="mount.MountFile.source_path"></a>
#### `source_path`

```python
 | def source_path() -> str
```

> Temporary file path name.

<a name="mount.MountFile.start"></a>
#### `start`

```python
 | def start() -> None
```

> Start the volume mount.

<a name="mount.MountFile.stop"></a>
#### `stop`

```python
 | def stop() -> None
```

> Stop the volume mount.

<a name="mount.MountPoint"></a>
#### `MountPoint`

```python
def MountPoint(*, template_name: str, target_path: str, template_variables: Optional[Dict[Any, Any]] = None) -> MountFile
```

> Context manager which yields a prepared instance of a docker volume.
> 
> **Arguments**:
> 
> - `template_name` _str_ - Name of the jinja template.
> - `target_path` _str_ - Local file system path.
> - `template_variables` _Optional[Dict[Any, Any]]_ - Jinja template variables.

