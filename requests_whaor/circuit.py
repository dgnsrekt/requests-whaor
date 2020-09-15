from requests_whaor.client import ContainerOptions, ContainerBase
from concurrent.futures import as_completed, ThreadPoolExecutor
from requests_whaor.constants import TOR_IMAGE

from typing import Optional
from docker.models.containers import Container
from contextlib import contextmanager

from loguru import logger


class OnionCircuit(ContainerBase):
    container_options: ContainerOptions = ContainerOptions(image=TOR_IMAGE)


@contextmanager
def OnionCircuits(
    onion_count,
    startup_with_threads=False,
    max_threads=2,
    thread_pool_timeout=None,
    show_log=False,
):
    onion_circuits = [OnionCircuit() for _ in range(onion_count)]

    try:
        if startup_with_threads:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = [
                    executor.submit(circuit.start, show_log=show_log) for circuit in onion_circuits
                ]

                for future in as_completed(futures, timeout=thread_pool_timeout):
                    future.result()

        else:
            for circuit in onion_circuits:
                circuit.start(show_log=show_log)

        yield onion_circuits

    finally:
        if startup_with_threads:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = [
                    executor.submit(circuit.stop, show_log=show_log) for circuit in onion_circuits
                ]

                for future in as_completed(futures, thread_pool_timeout):
                    future.result()

        else:
            for circuit in onion_circuits:
                circuit.stop(show_log=show_log)
