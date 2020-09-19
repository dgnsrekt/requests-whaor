import docker
from typing import ClassVar, List, Dict, Optional
from pydantic import BaseModel as Base
from docker.client import DockerClient
from docker.models.containers import Container
from docker.types import Mount as DockerMount
from tempfile import _TemporaryFileWrapper as TemporaryFile
from loguru import logger


class Client(Base):
    client: ClassVar[DockerClient] = None

    @classmethod
    def get_client(cls):
        if cls.client is None:
            cls.client = docker.from_env()

        cls.client.ping()
        logger.debug("Docker connection successful.")

        return cls.client

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            TemporaryFile: lambda temp: temp.name,
            Container: lambda container: container.name,
        }


class ContainerOptions(Base):
    container_timeout: ClassVar[int] = 5

    image: Optional[str]
    auto_remove: bool = True
    detach: bool = True
    detach: bool = True
    mounts: List[DockerMount] = list()
    ports: Dict[int, int] = dict()


class ContainerBase(Client):
    container_options: ContainerOptions = ContainerOptions()
    container: Optional[Container]

    @property
    def container_id(self):
        return self.container.id

    @property
    def container_short_id(self):
        return self.container.short_id

    @property
    def container_name(self):
        return self.container.name

    @property
    def container_timeout(self):
        return self.container_options.container_timeout

    def show_follow_logs_command(self):
        logger.info(f"Run the following command to show ({self.container_name}) containers logs.")
        logger.info(f"docker container logs -f {self.container_name}")

    def expose_port(self, port: int):
        self.container_options.ports[port] = port

    def restart(self, timeout=5):
        logger.debug(f"Restarting container {self.container_name} {self.container_short_id}.")
        self.container.restart(timeout=timeout)

    def start(self, show_log=False):
        client = self.get_client()

        self.container = client.containers.run(**self.container_options.dict())

        logger.debug(f"Running container {self.container_name} {self.container_short_id}.")

        if show_log:
            self.container.reload()

            for line in self.container.logs().decode().split("\n"):
                logger.debug(line)

    def stop(self, show_log=False):
        logger.debug(f"Stopping container {self.container_name} {self.container_short_id}.")

        if show_log:
            self.container.reload()

            for line in self.container.logs().decode().split("\n"):
                logger.debug(line)

        self.container.stop(timeout=self.container_timeout)

        logger.debug(f"Container {self.container_name} {self.container_short_id} Destroyed.")
