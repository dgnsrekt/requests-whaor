from requests_whaor.client import Client
from docker.models.volumes import Volume as DockerVolume
from docker.types import Mount
from typing import Optional, Dict, Any
from pydantic import validator

from requests_whaor.paths import TEMPLATE_DIRECTORY, TEMPORARY_FILES_DIRECTORY
from pathlib import Path
from tempfile import _TemporaryFileWrapper as TemporaryFile
from tempfile import NamedTemporaryFile
from jinja2 import Environment, FileSystemLoader
import string

from contextlib import contextmanager


class MountFile(Client):
    template_name: str
    target_path: str
    volume_driver: str = "local"

    temporary_file: Optional[TemporaryFile]
    mount: Optional[Mount]
    template_variables: Optional[Dict[Any, Any]]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {TemporaryFile: lambda temp: temp.name, DockerVolume: lambda vol: vol.name}

    @validator("template_name")
    def _template_must_exist(cls, template_name):
        template_path = TEMPLATE_DIRECTORY / template_name
        if template_path.exists():
            return template_name

        raise ValueError(f"{template_name} does not exist.")

    @property
    def volume_name(self):
        return self.template_name.replace(".", "_") + "_volume"

    @property
    def source_path(self):
        return self.temporary_file.name

    def _render_template(self):
        env = Environment(loader=FileSystemLoader(TEMPLATE_DIRECTORY), keep_trailing_newline=True)
        template = env.get_template(self.template_name)

        if self.template_variables:
            return template.render(self.template_variables)
        else:
            return template.render()

    def _create_source_file(self):
        self.temporary_file = NamedTemporaryFile(dir=TEMPORARY_FILES_DIRECTORY, suffix=".conf")

    def _generate_source_file(self):
        render_data = self._render_template()
        self._create_source_file()
        self.temporary_file.write(render_data.encode())
        self.temporary_file.seek(0)

    def _start(self):
        client = self.get_client()
        self._generate_source_file()
        self.mount = Mount(
            target=self.target_path, source=self.source_path, read_only=True, type="bind"
        )

    def _stop(self):
        if self.temporary_file:
            self.temporary_file.close()


@contextmanager
def MountPoint(*, template_name, target_path, template_variables=None):
    mount_file = MountFile(
        template_name=template_name, target_path=target_path, template_variables=template_variables
    )

    try:
        mount_file._start()

        yield mount_file

    finally:
        mount_file._stop()
