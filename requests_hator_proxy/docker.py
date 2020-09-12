from requests_hator_proxy.paths import TEMPLATE_DIRECTORY, PROJECT_ROOT_PATH

from tempfile import NamedTemporaryFile
from tempfile import _TemporaryFileWrapper as TemporaryFile

from typing import Optional

from pydantic import BaseModel as Base

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from loguru import logger


class ConfigBase(Base):
    name: str
    tempfile: Optional[TemporaryFile]
    docker_path: str

    @property
    def volume(self):
        # NOTE in the futures you may have to think about multiple volumes per container.

        volume = {"bind": self.docker_path, "mode": "ro"}
        print({self.tempfile.name: volume})
        return {self.tempfile.name: volume}

    @classmethod
    def create_config(cls, name: str, docker_path: str, render_data: Optional[dict] = None):
        obj = cls(name=name, docker_path=docker_path)
        obj._create_temporary_file(render_data)
        logger.debug(f"Created config file: \n{obj.json()}")
        return obj

    def _get_render_environment(self):
        return Environment(loader=FileSystemLoader(TEMPLATE_DIRECTORY))

    def _get_template(self):
        env = self._get_render_environment()
        return env.get_template(self.name)

    def _render(self, render_data: Optional[dict] = None):
        template = self._get_template()

        if render_data:
            return template.render(render_data) + "\n"
        else:
            return template.render() + "\n"

    def _create_temporary_file(self, render_data: Optional[dict] = None):
        config = self._render(render_data)
        self.tempfile = NamedTemporaryFile(dir=PROJECT_ROOT_PATH)
        self.tempfile.write(config.encode())
        self.tempfile.seek(0)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {TemporaryFile: lambda temp: temp.name}
