import docker
from typing import ClassVar
from pydantic import BaseModel as Base
from docker.client import DockerClient as Client
from docker.models.containers import Container
from tempfile import _TemporaryFileWrapper as TemporaryFile
from loguru import logger


class DockerClient(Base):
    client: ClassVar[Client] = None

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
