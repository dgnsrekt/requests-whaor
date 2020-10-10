"""This module provides objects for managing TOR docker instances."""

from concurrent.futures import as_completed, ThreadPoolExecutor
from contextlib import contextmanager
from typing import ContextManager, List, Optional

from .client import ContainerBase, ContainerOptions

TOR_IMAGE = "osminogin/tor-simple:0.4.3.6"


class OnionCircuit(ContainerBase):
    """A TOR Docker Container Object.

    Attributes:
        container_options (ContainerOptions): Container Options for TOR docker instance.
    """

    container_options: ContainerOptions = ContainerOptions(image=TOR_IMAGE)


@contextmanager
def OnionCircuits(  # pylint: disable=invalid-name
    onion_count: int,
    startup_with_threads: bool = False,
    max_threads: int = 2,
    thread_pool_timeout: Optional[int] = None,
    show_log: bool = False,
) -> ContextManager[List[OnionCircuit]]:
    """Context manager which yields a list of started TOR containers.

    Takes care of starting and stopping multiple docker container instances of TOR.

    Args:
        onion_count (int): Number of TOR docker container instances to start.
        start_with_threads (bool): If True uses threads to start up the containers.
        max_threads (int): Max number of threads to use to start up the containers.
        thread_pool_timeout (Optional[int]): Timeout for ThreadPoolExecutor.
        show_log (bool): If True shows the containers logs.

    Yields:
        List[OnionCircuit]: A list of started OnionCircuit objects.
    """
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
