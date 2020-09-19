from requests_whaor.network import WhaorNet
from requests_whaor.balancer import HAProxyOptions, OnionBalancer
from requests_whaor.circuit import OnionCircuits

from concurrent.futures import as_completed, ThreadPoolExecutor

import requests
from contextlib import contextmanager, ExitStack
import time
from loguru import logger

import random
from math import floor


class Requests:
    def __init__(self, proxies, onions, timeout=5):
        self.timeout = timeout
        self.proxies = proxies
        self.onions = onions

    @property
    def rotating_proxy(self):
        return self.proxies

    def get(self, url, *args, **kwargs):
        return requests.get(url, timeout=self.timeout, proxies=self.proxies, *args, **kwargs)

    def restart_onions(self, with_threads=True, max_threads=5):
        k = len(self.onions) // 2
        k = 1 if k <= 1 else k

        onions = random.sample(self.onions, k=k)
        print(f"restarting {k} onions")  # TODO: logging

        if with_threads:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = [executor.submit(onion.restart) for onion in onions]
                for future in as_completed(futures):
                    future.result()
        else:
            for onion in onions:
                onion.restart()

        time.sleep(1)


def pause(sleep):
    if random.random() > 0.5:
        logger.debug("Warming things up.")
    else:
        logger.debug("Just chillin for a sec.")

    time.sleep(sleep)  # let things connect


@contextmanager
def RequestsWhaor(
    onion_count=5, start_with_threads=True, max_threads=5, timeout=5, show_log=False
):
    with ExitStack() as stack:
        try:
            network = stack.enter_context(WhaorNet())
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

            pause(5)

            yield Requests(timeout=timeout, proxies=onion_balancer.proxies, onions=onions)

        finally:

            stack.pop_all().close()
