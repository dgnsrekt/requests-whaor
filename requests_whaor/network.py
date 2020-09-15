from requests_whaor.client import Client
from docker.models.networks import Network as DockerNetwork
from contextlib import contextmanager

from loguru import logger

from typing import Optional


class Network(Client):
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

    def start(self):
        client = self.get_client()
        self.docker_network = client.networks.create(name=self.name, driver=self.driver)
        logger.debug(f"Network: {self.network_name} {self.network_id} Created.")

    def stop(self):
        self.docker_network.reload()

        if self.docker_network.containers:

            for container in self.docker_network.containers:
                self.docker_network.disconnect(container.name)

        self.docker_network.remove()
        logger.debug(f"Network: {self.network_name} {self.network_id} Destroyed.")


@contextmanager
def Whaornet(name: str = "whaornet", driver: str = "bridge"):

    whaornet = Network(name=name, driver=driver)

    try:
        whaornet.start()
        yield whaornet

    finally:
        whaornet.stop()
