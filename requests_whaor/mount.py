"""This module provides objects for managing docker mount instances."""

from contextlib import contextmanager
from tempfile import _TemporaryFileWrapper as TemporaryFile
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Optional

from docker.models.volumes import Volume as DockerVolume
from docker.types import Mount
from jinja2 import Environment, FileSystemLoader
from pydantic import validator

from .client import Client
from .paths import TEMPLATE_DIRECTORY, TEMPORARY_FILES_DIRECTORY


class MountFile(Client):
    """Represents a file to be binded to a docker container.

    Attributes:
        template_name (str): Name of the jinja template.
        target_path (str): Local file system path.
        volume_driver (str): Type of docker volume.
        temporary_file (Optional[TemporaryFile]): A mounted instance of a TemporaryFile.
        mount (Optional[Mount]): An instance of the DockerMount.
        template_variables (Optional[Dict[Any, Any]]): Jinja template variables.
    """

    template_name: str
    target_path: str
    volume_driver: str = "local"

    temporary_file: Optional[TemporaryFile]
    mount: Optional[Mount]
    template_variables: Optional[Dict[Any, Any]]

    class Config:
        """Pydantic Configuration."""

        arbitrary_types_allowed = True
        json_encoders = {TemporaryFile: lambda temp: temp.name, DockerVolume: lambda vol: vol.name}

    @validator("template_name")
    def _template_must_exist(  # pylint: disable=no-self-argument,no-self-use
        cls, template_name: str
    ) -> str:
        """Check if template exists in template directory."""
        template_path = TEMPLATE_DIRECTORY / template_name
        if template_path.exists():
            return template_name

        raise ValueError(f"{template_name} does not exist.")

    @property
    def volume_name(self) -> str:
        """Name of the volume."""
        return self.template_name.replace(".", "_") + "_volume"

    @property
    def source_path(self) -> str:
        """Temporary file path name."""
        return self.temporary_file.name

    def _render_template(self) -> str:
        """Render jinja template."""
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIRECTORY), keep_trailing_newline=True)
        template = env.get_template(self.template_name)

        if self.template_variables:
            return template.render(self.template_variables)

        return template.render()

    def _create_source_file(self) -> None:
        """Create temp file for storing render template output."""
        self.temporary_file = NamedTemporaryFile(dir=TEMPORARY_FILES_DIRECTORY, suffix=".conf")

    def _generate_source_file(self) -> None:
        """Generate source file."""
        render_data = self._render_template()
        self._create_source_file()
        self.temporary_file.write(render_data.encode())
        self.temporary_file.seek(0)

    def start(self) -> None:
        """Start the volume mount."""
        self._generate_source_file()
        self.mount = Mount(
            target=self.target_path, source=self.source_path, read_only=True, type="bind"
        )

    def stop(self) -> None:
        """Stop the volume mount."""
        if self.temporary_file:
            self.temporary_file.close()


@contextmanager
# pylint: disable=invalid-name
def MountPoint(
    *, template_name: str, target_path: str, template_variables: Optional[Dict[Any, Any]] = None
) -> MountFile:
    """Context manager which yields a prepared instance of a docker volume.

    Args:
        template_name (str): Name of the jinja template.
        target_path (str): Local file system path.
        template_variables (Optional[Dict[Any, Any]]): Jinja template variables.
    """
    mount_file = MountFile(
        template_name=template_name, target_path=target_path, template_variables=template_variables
    )

    try:
        mount_file.start()
        yield mount_file

    finally:
        mount_file.stop()
