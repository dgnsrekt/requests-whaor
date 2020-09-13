from requests_haor.docker import DockerBase, DockerVolume

from typing import Optional, List
from docker.models.containers import Container

from loguru import logger


class LoadBalancer(DockerBase):
    image: str = "haproxy:latest"
    container: Optional[Container]
    config: Optional[DockerVolume]

    auto_remove: bool = True
    detach: bool = True
    container_timeout: int = 5

    max_connections: int = 4096

    timeout_client: int = 3600
    timeout_connect: int = 1
    timeout_queue: int = 5
    timeout_server: int = 3600

    host_name: str = "REQUESTS_HAOR"
    host_port: int = 8001

    backend_name: str = "ONION_CIRCUITS"

    dashboard_bind_port: int = 9999
    dashboard_refresh_rate: int = 2

    proxies: List[Container]

    class Config:
        arbitrary_types_allowed = True

    @property
    def host_address(self):
        return f"socks5://localhost:{self.host_port}"

    @property
    def dashboard_address(self):
        return f"http://localhost:{self.dashboard_bind_port}"

    @property
    def docker_exposed_ports(self):
        return {self.host_port: self.host_port, self.dashboard_bind_port: self.dashboard_bind_port}

    def _log_config_settings(self, render_data: dict):
        logger.debug("=================================")
        logger.debug("HAProxyLoadBalancer configuration")
        logger.debug("=================================")
        for key, value in render_data.items():
            if key == "proxies":
                logger.debug(f"{key}: {len(value)}")
                continue
            if value:
                logger.debug(f"{key}: {value}")

    def _create_docker_options(self):
        render_data = self.dict()

        self._log_config_settings(render_data)

        self.config = DockerVolume.render(
            "haproxy.cfg", "/usr/local/etc/haproxy/haproxy.cfg", render_data=render_data
        )

        options = {
            "image": self.image,
            "auto_remove": self.auto_remove,
            "detach": self.detach,
            "volumes": self.config.volume,
            "ports": self.docker_exposed_ports,
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
