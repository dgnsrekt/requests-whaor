import time

from requests_hator_proxy.docker import ConfigBase

from typing import Optional, ClassVar, List, Dict

from pydantic import BaseModel as Base

import docker
from docker.client import DockerClient
from docker.models.containers import Container
from docker.models.networks import Network
from docker.errors import NotFound
from loguru import logger

from pprint import pprint

from tempfile import _TemporaryFileWrapper as TemporaryFile

from abc import ABC, abstractmethod, abstractproperty, abstractclassmethod, abstractstaticmethod
import requests
from requests import Session
from requests.exceptions import ProxyError


class DockerBase(Base, ABC):
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
        json_encoders = {TemporaryFile: lambda temp: temp.name}

    @abstractmethod
    def _start(self):
        pass

    @abstractmethod
    def _stop(self):
        pass


class TorCircuit(DockerBase):
    # image: str = "dperson/torproxy:latest"
    image: str = "osminogin/tor-simple:latest"

    container: Optional[Container]
    config: ConfigBase

    auto_remove: bool = True
    detach: bool = True
    container_timeout: int = 5

    @classmethod
    def get_config(cls):
        return ConfigBase.create_config("torrc2", "/etc/tor/torrc")

    def _create_docker_options(self):
        options = {
            "image": self.image,
            "auto_remove": self.auto_remove,
            "detach": self.detach,
            # "volumes": self.config.volume,
        }
        return options

    def _start(self):
        client = self.get_client()

        docker_options = self._create_docker_options()

        self.container = client.containers.run(**docker_options)

        logger.debug(f"Running container {self.container.name} {self.container.short_id}.")
        return None

        # self.container.reload()
        # print(self.container.logs())

    def _stop(self):
        logger.debug(f"Stopping container {self.container.name} {self.container.short_id}.")

        self.container.stop(timeout=self.container_timeout)

        logger.debug(f"Container {self.container.name} {self.container.short_id} Destroyed.")

        logger.debug(f"Use the following code to stop any dangling containers.")
        logger.debug(f"docker stop $(docker ps -q --filter ancestor={self.image})")
        return None


from enum import Enum


class ProxyMode(Enum):
    http = 8118
    socks5 = 9050


class ProxyLoadBalancer(DockerBase):
    image: str = "haproxy:latest"
    container: Optional[Container]
    config: Optional[ConfigBase]

    auto_remove: bool = True
    detach: bool = True
    container_timeout: int = 5

    max_connections: int = 4096

    timeout_client: int = 3600
    timeout_connect: int = 1
    timeout_queue: int = 5
    timeout_server: int = 3600

    proxy_mode: ProxyMode = ProxyMode.socks5

    host_name: str = "PROXY_LOAD_BALANCER"
    host_port: int = 8001

    backend_name: str = "TOR_CIRCUITS"

    dashboard_bind_port: int = 9999
    dashboard_refresh_rate: int = 2

    proxies: List[Container]

    class Config:
        arbitrary_types_allowed = True

    @property
    def host_address(self):
        return f"{self.proxy_mode.name}://localhost:{self.host_port}"

    @property
    def dashboard_address(self):
        return f"http://localhost:{self.dashboard_bind_port}"

    @property
    def docker_exposed_ports(self):
        return {self.host_port: self.host_port, self.dashboard_bind_port: self.dashboard_bind_port}

    def _log_config_settings(self, render_data: dict):
        logger.debug("ProxyLoadBalancer configuration settings.")
        logger.debug("=========================================")
        for key, value in render_data.items():
            if key == "proxies":
                logger.debug(f"{key}: {len(value)}")
                continue
            if value:
                logger.debug(f"{key}: {value}")

    def _create_docker_options(self):
        render_data = self.dict()
        render_data["mode"] = "http" if self.proxy_mode.name == "http" else "tcp"
        render_data["option_log"] = "httplog" if self.proxy_mode.name == "http" else "tcplog"

        self._log_config_settings(render_data)

        self.config = ConfigBase.create_config(
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

        logger.debug(f"Use the following code to stop any dangling containers.")
        logger.debug(f"docker stop $(docker ps -q --filter ancestor={self.image})")


class DockerNetwork(DockerBase):
    name: str = "requestor_network"
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


from requests.exceptions import Timeout, ConnectionError
from multiprocessing import cpu_count
from concurrent.futures import as_completed, ProcessPoolExecutor
from collections import Counter
import webbrowser
from contextlib import contextmanager
import enlighten


@contextmanager
def Requestor(*, proxy_count, proxy_mode, max_threads=3, open_dashboard=False):
    from concurrent.futures import as_completed, ThreadPoolExecutor

    tor_config = TorCircuit.get_config()

    proxies = [TorCircuit(config=tor_config) for _ in range(proxy_count)]

    network = DockerNetwork()
    network._start()

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(proxy._start) for proxy in proxies]

        for future in as_completed(futures, timeout=5):
            future.result()

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [
            executor.submit(network.connect, proxy.container.id, aliases=[proxy.container.name])
            for proxy in proxies
        ]

        for future in as_completed(futures, timeout=5):
            future.result()

    load_balancer = ProxyLoadBalancer(proxies=network.containers, proxy_mode=ProxyMode[proxy_mode])

    load_balancer._start()

    network.connect(load_balancer.container.id)

    logger.info(f"Sleeping 5 seconds to let everything warm up.")
    time.sleep(5)

    session_proxies = {"http": load_balancer.host_address, "https": load_balancer.host_address}

    if open_dashboard:
        webbrowser.open_new_tab(load_balancer.dashboard_address)
    else:
        logger.info(f"Dashboard Address: {load_balancer.dashboard_address}")

    try:
        session = Session()
        session.proxies = session_proxies
        yield session

    finally:
        load_balancer._stop()

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [executor.submit(proxy._stop) for proxy in proxies]

            for future in as_completed(futures, timeout=5):
                future.result()

        network._stop()

        load_balancer.config.tempfile.close()

        tor_config.tempfile.close()


def get_and_retry_recursively(url, session, retry=5):
    try:
        response = session.get(url, timeout=5)
        if response.ok:
            # return response.status_code
            return "PASSED"
            # return response.text

    except (ProxyError, Timeout, ConnectionError) as e:
        logger.error(e)
        logger.error(f"Will retry ({retry}) more times.")

    if retry > 0:
        retry -= 1

    else:
        return "FAILED"

    return get_and_retry_recursively(url, session, retry=retry)


from collections import Counter
import sys

# logger.remove(0)
# logger.add(sys.stdout, colorize=True, format="{time} {level} {message}", level="INFO")

url = "https://finance.yahoo.com/quote/TSLA/financials?p=TSLA"
url = "http://jsonip.com/"
url = "https://www.bitmex.com/api/v1/chat?count=100&reverse=true"

REQUESTS_TO_SEND = 25

cpus = cpu_count() - 2
proxy_count = cpus * 2

###################################################################################################
DESCRIPTION = "VANILLA REQUESTS SESSION + ProcessPoolExecutor TRYING NOT BACKING DOWN"
start = time.time()

results = []
with ProcessPoolExecutor(max_workers=cpus) as executor:
    session = Session()
    futures = [
        executor.submit(get_and_retry_recursively, url, session) for n in range(REQUESTS_TO_SEND)
    ]

    pbar = enlighten.Counter(total=REQUESTS_TO_SEND, desc=DESCRIPTION, unit="resp")
    for future in as_completed(futures):
        results.append(future.result())
        pbar.update()

end = time.time()

print("took:", (end - start) / 60)
print(Counter(results))

while True:
    print("LETS TRY THIS AGAIN!!!!")

    ###################################################################################################
    DESCRIPTION = "REQUESTOR SESSION + ProcessPoolExecutor NOT BACKING DOWN"
    start = time.time()

    results = []
    with Requestor(proxy_count=proxy_count, proxy_mode="socks5") as session:
        with ProcessPoolExecutor(max_workers=cpus) as executor:

            futures = [
                executor.submit(get_and_retry_recursively, url, session)
                for n in range(REQUESTS_TO_SEND)
            ]

            pbar = enlighten.Counter(total=REQUESTS_TO_SEND, desc=DESCRIPTION, unit="resp")

            for future in as_completed(futures, timeout=60):
                results.append(future.result())
                pbar.update()

    end = time.time()

    print("took:", (end - start) / 60)
    print(Counter(results))

    print("done")
    print("time.sleep(15)")
    time.sleep(15)

print(
    """
You may need this.

docker stop $(docker ps -q --filter ancestor=dperson/torproxy:latest)
docker stop $(docker ps -q --filter ancestor=haproxy:latest)
docker network prune

"""
)
