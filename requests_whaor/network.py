"""This module provides objects for managing docker network instances."""

from contextlib import contextmanager
from typing import ContextManager, List, Optional

from docker.models.containers import Container as DockerContainer
from docker.models.networks import Network as DockerNetwork
from loguru import logger

from .client import Client


class Network(Client):
    """Represents a docker network.

    Attributes:
        name (str): Network name.
        driver (str): Network driver.
        docker_network (Optional[DockerNetwork]): Holds an instance of a started docker network.
    """

    name: str
    driver: str

    docker_network: Optional[DockerNetwork]

    def connect_container(self, container_id: str, container_name: str) -> None:
        """Connect container to network and give it a reachable network alias.

        Args:
            container_id (str): The containers id.
            container_name (str): The containers name.
        """
        logger.debug(f"connecting {container_name} to the {self.network_name} network")
        self.docker_network.connect(container_id, aliases=[container_name])

    @property
    def containers(self) -> List[DockerContainer]:
        """Return list of Container objects connected to network."""
        self.docker_network.reload()
        return self.docker_network.containers

    @property
    def network_name(self) -> str:
        """Network name."""
        return self.docker_network.name

    @property
    def network_id(self) -> str:
        """Network short id."""
        return self.docker_network.short_id

    def start(self) -> None:
        """Start Docker network."""
        client = self.get_client()
        self.docker_network = client.networks.create(name=self.name, driver=self.driver)
        logger.debug(f"Network: {self.network_name} {self.network_id} Created.")

    def stop(self) -> None:
        """Stop Docker network."""
        self.docker_network.reload()

        if self.docker_network.containers:

            for container in self.docker_network.containers:
                self.docker_network.disconnect(container.name)

        self.docker_network.remove()
        logger.debug(f"Network: {self.network_name} {self.network_id} Destroyed.")


@contextmanager
# pylint: disable=invalid-name
def WhaorNet(name: str = "whaornet", driver: str = "bridge") -> ContextManager[Network]:
    """Context manager which yields a network to connect containers to.

    Args:
        name (str): Name of network.
        driver (str): Type of network drivier.

    Yields:
        Network: A Docker network.
    """
    whaornet = Network(name=name, driver=driver)

    try:
        whaornet.start()
        yield whaornet

    finally:
        whaornet.stop()
