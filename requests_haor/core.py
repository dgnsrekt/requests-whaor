from contextlib import contextmanager
from loguru import logger
from requests_hator_proxy.onion import OnionCircuit
from requests_hator_proxy.load_balancer import LoadBalancer
from requests_hator_proxy.network import HaorNetwork
from concurrent.futures import as_completed, ThreadPoolExecutor
from requests import Session

import time


def show_docker_debugging_commands():
    logger.debug("To stop any dangling containers.")
    logger.debug("docker stop $(docker ps -q --filter ancestor=haproxy:latest)")
    logger.debug("docker stop $(docker ps -q --filter ancestor=osminogin/tor-simple:latest)")
    logger.debug("docker network rm $(docker network ls -q -f name=requestor_network)")


@contextmanager
def RequestHaor(*, proxy_count, max_threads=2, open_dashboard=False):

    show_docker_debugging_commands()

    logger.info(f"Warming up HaorNetwork.")

    proxies = [OnionCircuit() for _ in range(proxy_count)]

    network = HaorNetwork()
    network._start()

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(proxy._start) for proxy in proxies]

        for future in as_completed(futures, timeout=proxy_count):
            future.result()

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [
            executor.submit(network.connect, proxy.container.id, aliases=[proxy.container.name])
            for proxy in proxies
        ]

        for future in as_completed(futures, timeout=proxy_count):
            future.result()

    load_balancer = LoadBalancer(proxies=network.containers)

    load_balancer._start()

    network.connect(load_balancer.container.id)

    logger.info(f"The HaorNetwork is ready to play.")
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

            for future in as_completed(futures, timeout=proxy_count):
                future.result()

        network._stop()
