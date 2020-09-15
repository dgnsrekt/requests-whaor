from requests_whaor.client import ContainerBase, ContainerOptions
from requests_whaor.mount import MountFile, MountPoint
from requests_whaor.constants import HAPROXY_IMAGE

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

    listen_host_port: int = 8001

    backend_name: str = "onions"

    dashboard_bind_port: int = 9999
    dashboard_refresh_rate: int = 2

    onions: List[Container]

    class Config:
        arbitrary_types_allowed = True

    @property
    def ports(self):
        return [self.listen_host_port, self.dashboard_bind_port]


class Balancer(ContainerBase):
    haproxy_options: HAProxyOptions

    container_options: ContainerOptions = ContainerOptions(image=HAPROXY_IMAGE)

    class Config:
        arbitrary_types_allowed = True

    @property
    def address(self):
        return f"socks5://localhost:{self.haproxy_options.listen_host_port}"

    @property
    def dashboard_address(self):
        return f"http://localhost:{self.haproxy_options.dashboard_bind_port}"

    @property
    def proxies(self):
        return {
            "http": self.address,
            "https": self.address,
        }

    def add_mount_point(self, mount: MountFile):
        self.container_options.mounts.append(mount.mount)

    def display_settings(self):
        logger.debug(
            "\n==================="
            "\nOnion Load Balancer"
            "\n==================="
            "\n" + self.json(indent=4)
        )
        self.show_follow_logs_command()


@contextmanager
def OnionBalancer(onions, show_log=False):
    haproxy_options = HAProxyOptions(onions=onions)

    with MountPoint(
        template_name="haproxy.cfg",
        target_path="/usr/local/etc/haproxy/haproxy.cfg",
        template_variables=haproxy_options.dict(),
    ) as mount_point:

        try:
            balancer = Balancer(haproxy_options=haproxy_options)
            balancer.add_mount_point(mount_point)

            for port in haproxy_options.ports:
                balancer.expose_port(port)

            balancer.start(show_log=show_log)
            balancer.display_settings()

            yield balancer

        finally:
            balancer.stop(show_log=show_log)
