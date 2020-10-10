"""This module provides objects for managing the network balancer."""

from contextlib import contextmanager
from typing import Dict, List

from docker.models.containers import Container
from loguru import logger
from pydantic import BaseModel as Base

from .circuit import OnionCircuit
from .client import ContainerBase, ContainerOptions
from .mount import MountFile, MountPoint

HAPROXY_IMAGE = "haproxy:2.2.3"


class HAProxyOptions(Base):
    """Handles options for HAProxy docker instance.

    Attributes:
        max_connections (int): Maximum per-process number of concurrent connections.
        timeout_client (int): Maximum inactivity time on the client side.
        timeout_connect (int): Maximum time to wait for a connection attempt to a server
            to succeed.
        timeout_queue (int): Maximum time to wait in the queue for a connection slot
            to be free.
        timeout_server (int): Maximum inactivity time on the server side.
        listen_host_port (int): Frontend port to the proxy.
        backend_name (str): Name of Backend section.
        dashboard_bind_port (int): Port to open to reach the HAProxy dashboard.
        dashboard_refresh_rate (int): Refresh rate of the HAProxy dashboard page.
        onions (List[Container]): Each onion container that is connected to the whaornet.
    """

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
        """Pydantic Configuration."""

        arbitrary_types_allowed = True

    @property
    def ports(self) -> List[int]:
        """Ports which will be used to expose on the local network."""
        return [self.listen_host_port, self.dashboard_bind_port]


class Balancer(ContainerBase):
    """HAProxy Load Balancer.

    Attributes:
        haproxy_options (HAProxyOptions): HAProxy options object.
        container_options (ContainerOptions): Container options for the HA proxy instance.
    """

    haproxy_options: HAProxyOptions

    container_options: ContainerOptions = ContainerOptions(image=HAPROXY_IMAGE)

    class Config:
        """Pydantic Configuration."""

        arbitrary_types_allowed = True

    @property
    def address(self) -> str:
        """Return socks5 address to poxy requests through."""
        return f"socks5://localhost:{self.haproxy_options.listen_host_port}"

    @property
    def dashboard_address(self) -> str:
        """Return full dashboard address."""
        return f"http://localhost:{self.haproxy_options.dashboard_bind_port}"

    @property
    def proxies(self) -> Dict[str, str]:
        """Return proxies to mount onto a requests session."""
        return {
            "http": self.address,
            "https": self.address,
        }

    def add_mount_point(self, mount: MountFile) -> None:
        """Mount a volume into the HAProxy container.

        Args:
            mount (MountFile): File to mount between the container and local file system.
        """
        self.container_options.mounts.append(mount.mount)

    def display_settings(self) -> None:
        """Log config settings to stdout."""
        logger.debug(
            "\n==================="
            "\nOnion Load Balancer"
            "\n==================="
            "\n" + self.json(indent=4)
        )
        self.show_follow_logs_command()


@contextmanager
# pylint: disable=invalid-name
def OnionBalancer(onions: List[OnionCircuit], show_log: bool = False) -> Balancer:
    """Context manager which yields a started instance of an HAProxy docker container.

    Args:
        onions (List[OnionCircuit]): List of tor containers to load balance requests across.
        show_log (bool): If True shows the HAProxies logs on start and stop.

    Yields:
        Balancer: A started instance of a HAProxy docker container.
    """
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
