"""This module provides base objects to manage docker containers."""

from tempfile import _TemporaryFileWrapper as TemporaryFile
from typing import ClassVar, Dict, List, Optional

import docker
from docker.client import DockerClient
from docker.models.containers import Container
from docker.types import Mount as DockerMount
from loguru import logger
from pydantic import BaseModel as Base


class Client(Base):
    """A Docker Client.

    Provides the methods to connect to a docker engine.

    Attributes:
        client (ClassVar[DockerClient]): A shared docker client session.
    """

    client: ClassVar[DockerClient] = None

    @classmethod
    def get_client(cls) -> DockerClient:
        """Return the docker client."""
        if cls.client is None:
            cls.client = docker.from_env()

        cls.client.ping()
        logger.debug("Docker connection successful.")

        return cls.client

    class Config:
        """Pydantic Configuration."""

        arbitrary_types_allowed = True
        json_encoders = {
            TemporaryFile: lambda temp: temp.name,
            Container: lambda container: container.name,
        }


class ContainerOptions(Base):
    """Docker Container Options.

    Provides common options needed to start a docker container.

    Attributes:
        container_timeout (ClassVar[int]): Timeout in seconds to wait for the container
            to stop before sending a SIGKILL.
        image (Optional[str]): Name of docker image.
        auto_remove (bool): Enable auto-removal of the container on daemon side when the
            container’s process exits.
        detach (bool): Run container in the background and return a Container object.
        mounts (List[DockerMount]): Specification for mounts to be added to the container.
        ports (Dict[int, int]): Ports to bind inside the container.
    """

    container_timeout: ClassVar[int] = 5

    image: Optional[str]
    auto_remove: bool = True
    detach: bool = True
    mounts: List[DockerMount] = list()
    ports: Dict[int, int] = dict()


class ContainerBase(Client):
    """Docker Container Base with default options and commonly used methods.

    Attributes:
        container_options (ContainerOptions): ContainerOptions Object.
        container (Optional[Container]): Holds an instance of a initiated docker container.
    """

    container_options: ContainerOptions = ContainerOptions()
    container: Optional[Container]

    @property
    def container_id(self) -> str:
        """Return container instance id."""
        return self.container.id

    @property
    def container_short_id(self) -> str:
        """Return container instance short id."""
        return self.container.short_id

    @property
    def container_name(self) -> str:
        """Return container instance name."""
        return self.container.name

    @property
    def container_timeout(self) -> int:
        """Return container timeout."""
        return self.container_options.container_timeout

    def show_follow_logs_command(self) -> None:
        """Print log message with docker container logs command."""
        logger.info(f"Run the following command to show ({self.container_name}) containers logs.")
        logger.info(f"docker container logs -f {self.container_name}")

    def expose_port(self, port: int) -> None:
        """Add ports to expose to the container options.

        Args:
            port (int): The port to expose.
        """
        self.container_options.ports[port] = port

    def start(self, show_log: bool = False) -> None:
        """Start a container instance.

        Args:
            show_log (bool): If True shows the containers logs.
        """
        client = self.get_client()

        self.container = client.containers.run(**self.container_options.dict())

        logger.debug(f"Running container {self.container_name} {self.container_short_id}.")

        if show_log:
            self.print_logs()

    def restart(self) -> None:
        """Restart the container instance."""
        logger.debug(f"Restarting container {self.container_name} {self.container_short_id}.")
        self.container.restart(timeout=self.container_timeout)

    def print_logs(self) -> None:
        """Print the container instance logs."""
        self.container.reload()

        for line in self.container.logs().decode().split("\n"):
            logger.debug(line)

    def stop(self, show_log: bool = False) -> None:
        """Stop a container instance.

        Args:
            show_log (bool): If True shows the containers logs.
        """
        logger.debug(f"Stopping container {self.container_name} {self.container_short_id}.")

        if show_log:
            self.print_logs()

        self.container.stop(timeout=self.container_timeout)

        logger.debug(f"Container {self.container_name} {self.container_short_id} Destroyed.")
