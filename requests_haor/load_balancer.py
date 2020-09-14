from requests_haor.docker_client import DockerClient
from requests_haor.volume_mount import VolumeFile, VolumeMount

from typing import Optional, List
from docker.models.containers import Container

from pydantic import BaseModel as Base

from loguru import logger
from contextlib import contextmanager


class HAProxyOptions(Base):
    max_connections: int = 4096

    timeout_client: int = 3600
    timeout_connect: int = 1
    timeout_queue: int = 5
    timeout_server: int = 3600

    host_name: str = "REQUESTS_HAOR_NETWORK"
    host_port: int = 8001

    backend_name: str = "ONION_CIRCUITS"

    dashboard_bind_port: int = 9999
    dashboard_refresh_rate: int = 2

    proxies: List[Container]

    class Config:
        arbitrary_types_allowed = True


class LoadBalancer(DockerClient):
    image: str = "haproxy:latest"

    container: Optional[Container]

    volume_mount: VolumeFile

    auto_remove: bool = True
    detach: bool = True
    container_timeout: int = 5

    haproxy_options: HAProxyOptions

    class Config:
        arbitrary_types_allowed = True

    @property
    def session_proxy(self):
        return {
            "http": self.host_address,
            "https": self.host_address,
        }

    @property
    def container_id(self):
        return self.container.id

    @property
    def container_name(self):
        return self.container.name

    @property
    def host_address(self):
        return f"socks5://localhost:{self.haproxy_options.host_port}"

    @property
    def dashboard_address(self):
        return f"http://localhost:{self.haproxy_options.dashboard_bind_port}"

    @property
    def expose_ports(self):
        return {
            self.haproxy_options.host_port: self.haproxy_options.host_port,
            self.haproxy_options.dashboard_bind_port: self.haproxy_options.dashboard_bind_port,
        }

    def _log_config_settings(self, render_data: dict):
        logger.debug(
            "\n================================="
            "\nHAProxyLoadBalancer configuration"
            "\n================================="
        )
        logger.debug("\n" + self.json(indent=4))

    def _create_docker_options(self):
        render_data = self.dict()

        self._log_config_settings(render_data)

        options = {
            "image": self.image,
            "auto_remove": self.auto_remove,
            "detach": self.detach,
            "mounts": [self.volume_mount.mount],
            "ports": self.expose_ports,
        }
        return options

    def _start(self, initial_logging=False):
        client = self.get_client()

        docker_options = self._create_docker_options()

        self.container = client.containers.run(**docker_options)

        logger.debug(f"Running container {self.container.name} {self.container.short_id}.")

        self.container.reload()

        if initial_logging:

            for line in self.container.logs().decode().split("\n"):
                logger.debug(line)

    def _stop(self, initial_logging=False):
        logger.debug(f"Stopping container {self.container.name} {self.container.short_id}.")
        if initial_logging:

            for line in self.container.logs().decode().split("\n"):
                logger.debug(line)

        self.container.stop(timeout=self.container_timeout)

        logger.debug(f"Container {self.container.name} {self.container.short_id} Destroyed.")


@contextmanager
def LoadManager(haornet_containers):
    haproxy_options = HAProxyOptions(proxies=haornet_containers)
    with VolumeMount(
        template_name="haproxy.cfg",
        target_path="/usr/local/etc/haproxy/haproxy.cfg",
        template_variables=haproxy_options.dict(),
    ) as volume_mount:

        try:
            load_balancer = LoadBalancer(
                haproxy_options=haproxy_options, volume_mount=volume_mount
            )
            load_balancer._start()

            yield load_balancer

        finally:
            load_balancer._stop()
