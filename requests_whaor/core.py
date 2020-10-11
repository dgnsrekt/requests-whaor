"""This module provides core requests_whaor functionality."""

from concurrent.futures import as_completed, ThreadPoolExecutor
from contextlib import contextmanager, ExitStack
import random
import time
from typing import Dict, List, Optional

from loguru import logger
import requests
from requests.exceptions import (  # pylint: disable=redefined-builtin
    ConnectionError,
    ProxyError,
    Timeout,
)

from .balancer import Balancer, OnionBalancer
from .circuit import OnionCircuit, OnionCircuits
from .network import WhaorNet


def pause(sleep: int) -> None:
    """Sleep function with a little logging fun."""
    if random.random() > 0.5:
        logger.debug("Warming things up.")
    else:
        logger.debug("Just chillin for a sec.")

    time.sleep(sleep)  # let things connect


class Requestor:
    """Makes proxied web requests via a rotating proxy TOR network."""

    def __init__(
        self, onions: List[OnionCircuit], onion_balancer: Balancer, timeout: int, max_retries: int
    ) -> "Requestor":
        """Requestor __init__ method.

        Args:
            onions (List[OnionCircuit]): List of TOR containers.
            onion_balancer (Balancer): Balancer instances connected to TOR containers
                on the same network.
            timeout (int): Requests timeout.
            max_retries (int): Max number of time to retry on bad response or connection error.
        """
        self.timeout = timeout
        self.onions = onions
        self.onion_balancer = onion_balancer
        self.max_retries = max_retries

    @property
    def rotating_proxy(self) -> Dict[str, str]:
        """Rotating proxy frontend input address."""
        return self.onion_balancer.proxies

    def get(
        self, url: str, *args, **kwargs  # noqa: ANN002, ANN003
    ) -> Optional[requests.models.Response]:
        """Overload requests.get method.

        This will pass in the rotating proxy host address and timeout into the requests.get
        method. Additionally, It provides a way to automatically retry on connection failures
        and bad status_codes. Each time there is a failure it will try a new request with
        a new ip address.

        Args:
            url (str): url to send the get request.
            *args: arguments to pass to requests.get() method.
            **kwargs: keyword arguments to pass to requests.get() method.

        Returns:
            Response: If a response is found else None.
        """
        retries = self.max_retries

        kwargs.pop("proxies", None)
        kwargs.pop("timeout", None)

        while retries > 0:
            try:
                response = requests.get(
                    url, timeout=self.timeout, proxies=self.rotating_proxy, *args, **kwargs
                )
                if response.ok:
                    return response

            except (ProxyError, Timeout, ConnectionError) as error:
                logger.error(error)

            retries -= 1
            logger.debug(f"Retrying {retries} more times.")

        return None

    def restart_onions(self, with_threads: bool = True, max_threads: int = 5) -> None:
        """Restart onion containers.

        This can be useful for changing ip addresses every n requests.

        Args:
            with_threads (bool): if True uses threads to restart the containers.
            max_threads (int): How many threads to use.
        """
        if with_threads:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = [executor.submit(onion.restart) for onion in self.onions]

                for future in as_completed(futures):
                    future.result()
        else:
            for onion in self.onions:
                onion.restart()

        pause(5)


@contextmanager
def RequestsWhaor(  # pylint: disable=invalid-name, too-many-arguments
    onion_count: int = 5,
    start_with_threads: bool = True,
    max_threads: int = 5,
    timeout: int = 5,
    show_log: bool = False,
    max_retries: int = 5,
) -> Requestor:
    """Context manager which starts n amount of tor nodes behind a round robin reverse proxy.

    Args:
        onion_count (int): Number of TOR circuits to spin up.
        start_with_threads (bool): If True uses treads to spin up containers.
        max_threads (int): Max number of threads to use when spin up containers.
        timeout (int): Requests timeout.
        show_log (bool): If True shows the containers logs.
        max_retries (int): Max number of time to retry on bad response or connection error.

    Yields:
        Requestor: Makes proxied web requests via a rotating proxy TOR network.
    """
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

            pause(5)

            logger.info(f"Dashboard Address: {onion_balancer.dashboard_address}")

            pause(1)

            yield Requestor(
                onions=onions,
                onion_balancer=onion_balancer,
                timeout=timeout,
                max_retries=max_retries,
            )

        finally:

            stack.pop_all().close()
