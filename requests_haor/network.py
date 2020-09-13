from requests_haor.docker_client import DockerClient
from docker.models.networks import Network as DockerNetwork
from contextlib import contextmanager

from loguru import logger

from typing import Optional


class Network(DockerClient):
    name: str
    driver: str

    docker_network: Optional[DockerNetwork]

    def connect_container(self, container_id, container_name):
        logger.debug(f"{container_name} to {self.network_name}")
        return self.docker_network.connect(container_id, aliases=[container_name])

    @property
    def containers(self):
        self.docker_network.reload()
        return self.docker_network.containers

    @property
    def network_name(self):
        return self.docker_network.name

    @property
    def network_id(self):
        return self.docker_network.short_id

    def _start(self):
        client = self.get_client()
        self.docker_network = client.networks.create(name=self.name, driver=self.driver)
        logger.debug(f"Network: {self.network_name} {self.network_id} Created.")

    def _stop(self):
        if self.docker_network:
            self.docker_network.remove()
            logger.debug(f"Network: {self.network_name} {self.network_id} Destroyed.")


@contextmanager
def Haornet(name: str = "haornet", driver: str = "bridge"):

    haornet = Network(name=name, driver=driver)

    try:
        haornet._start()
        yield haornet

    finally:
        haornet._stop()
