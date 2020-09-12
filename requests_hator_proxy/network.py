from requests_hator_proxy.docker import DockerBase
from docker.models.networks import Network

from loguru import logger

from typing import Optional


class HaorNetwork(DockerBase):
    name: str = "HaorNetwork"
    driver: str = "bridge"

    network: Optional[Network]

    def connect(self, *args, **kwargs):
        return self.network.connect(*args, **kwargs)

    @property
    def containers(self):
        self.network.reload()
        return self.network.containers

    def _start(self):
        client = self.get_client()
        self.network = client.networks.create(name=self.name, driver=self.driver)
        logger.debug(f"Network: {self.network.name} {self.network.short_id} Created.")

    def _stop(self):
        if self.network:
            self.network.remove()
            logger.debug(f"Network: {self.network.name} {self.network.short_id} Destroyed.")
