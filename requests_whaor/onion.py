from requests_whaor.docker_client import DockerClient
from concurrent.futures import as_completed, ThreadPoolExecutor

from typing import Optional
from docker.models.containers import Container
from contextlib import contextmanager

from loguru import logger


class TorCircuit(DockerClient):
    image: str = "osminogin/tor-simple:latest"

    container: Optional[Container]

    auto_remove: bool = True
    detach: bool = True
    container_timeout: int = 5

    @property
    def container_id(self):
        return self.container.id

    @property
    def container_name(self):
        return self.container.name

    def _create_docker_options(self):
        options = {
            "image": self.image,
            "auto_remove": self.auto_remove,
            "detach": self.detach,
        }
        return options

    def _start(self, initial_logging=False):
        client = self.get_client()

        docker_options = self._create_docker_options()

        self.container = client.containers.run(**docker_options)

        logger.debug(f"Running container {self.container.name} {self.container.short_id}.")

        if initial_logging:

            for line in self.container.logs().decode().split("\n"):
                logger.debug(line)

    def _stop(self):
        logger.debug(f"Stopping container {self.container.name} {self.container.short_id}.")

        self.container.stop(timeout=self.container_timeout)

        logger.debug(f"Container {self.container.name} {self.container.short_id} Destroyed.")


@contextmanager
def OnionCircuits(
    onion_count,
    startup_with_threads=False,
    max_threads=2,
    thread_pool_timeout=None,
    initial_logging=False,
):
    circuits = [TorCircuit() for _ in range(onion_count)]

    try:
        if startup_with_threads:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = [
                    executor.submit(tor_circuit._start, initial_logging=initial_logging)
                    for tor_circuit in circuits
                ]

                for future in as_completed(futures, timeout=thread_pool_timeout):
                    future.result()

        else:
            for tor_circuit in circuits:
                tor_circuit._start()

        yield circuits

    finally:
        if startup_with_threads:
            with ThreadPoolExecutor(max_workers=max_threads) as executor:
                futures = [executor.submit(tor_circuit._stop) for tor_circuit in circuits]

                for future in as_completed(futures, thread_pool_timeout):
                    future.result()

        else:
            for tor_circuit in circuits:
                tor_circuit._stop()
