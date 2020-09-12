from requests_hator_proxy.docker import DockerBase

from typing import Optional
from docker.models.containers import Container

from loguru import logger


class OnionCircuit(DockerBase):
    image: str = "osminogin/tor-simple:latest"

    container: Optional[Container]

    auto_remove: bool = True
    detach: bool = True
    container_timeout: int = 5

    def _create_docker_options(self):
        options = {
            "image": self.image,
            "auto_remove": self.auto_remove,
            "detach": self.detach,
        }
        return options

    def _start(self):
        client = self.get_client()

        docker_options = self._create_docker_options()

        self.container = client.containers.run(**docker_options)

        logger.debug(f"Running container {self.container.name} {self.container.short_id}.")

    def _stop(self):
        logger.debug(f"Stopping container {self.container.name} {self.container.short_id}.")

        self.container.stop(timeout=self.container_timeout)

        logger.debug(f"Container {self.container.name} {self.container.short_id} Destroyed.")
