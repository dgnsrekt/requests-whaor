from requests_whaor.network import Whaornet
from requests_whaor.balancer import HAProxyOptions, OnionBalancer
from requests_whaor.circuit import OnionCircuits

import requests
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
    onion_count=5, start_with_threads=True, max_threads=5, timeout=5, show_log=False
):
    with ExitStack() as stack:
        try:
            network = stack.enter_context(Whaornet())
            onions = stack.enter_context(
                OnionCircuits(
                    onion_count,
                    startup_with_threads=start_with_threads,
                    max_threads=max_threads,
                    show_log=show_log,
                )
            )
            for onion in onions:
                network.connect_container(onion.container_id, onion.container_name)

            onion_balancer = stack.enter_context(
                OnionBalancer(onions=network.containers, show_log=show_log)
            )

            network.connect_container(onion_balancer.container_id, onion_balancer.container_name)

            logger.info(f"Dashboard Address: {onion_balancer.dashboard_address}")
            logger.debug("Warming things up.")
            time.sleep(5)  # let things connect

            yield Requests(timeout=timeout, proxies=onion_balancer.proxies)

        finally:

            stack.pop_all().close()
