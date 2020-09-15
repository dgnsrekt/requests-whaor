from requests_whaor.network import Haornet
from requests_whaor.load_balancer import LoadBalancer, HAProxyOptions, LoadManager
from requests_whaor.onion import OnionCircuits
from requests_whaor.volume_mount import VolumeMount

from docker.types import Mount
from requests import Session
import requests
from functools import partial
from contextlib import contextmanager, ExitStack
import time
from loguru import logger


class Requests:
    def __init__(self, proxies, timeout=5):
        self.timeout = timeout
        self.proxies = proxies

    @property
    def rotating_proxy(self):
        return self.proxies

    def get(self, url, *args, **kwargs):
        return requests.get(url, timeout=self.timeout, proxies=self.proxies, *args, **kwargs)


@contextmanager
def RequestsWhaor(
    proxy_count=5, start_with_threads=True, max_threads=5, timeout=5, initial_logging=False
):
    with ExitStack() as stack:
        try:
            haornet = stack.enter_context(Haornet())
            proxies = stack.enter_context(
                OnionCircuits(
                    proxy_count,
                    startup_with_threads=start_with_threads,
                    max_threads=max_threads,
                    initial_logging=initial_logging,
                )
            )
            for proxy in proxies:
                haornet.connect_container(proxy.container_id, proxy.container_name)

            load_balancer = stack.enter_context(LoadManager(haornet_containers=haornet.containers))

            haornet.connect_container(load_balancer.container_id, load_balancer.container_name)

            logger.info(f"Dashboard Address: {load_balancer.dashboard_address}")
            logger.debug("Warming things up.")
            time.sleep(5)  # let things connect

            yield Requests(timeout=timeout, proxies=load_balancer.session_proxy)

        finally:

            stack.pop_all().close()
