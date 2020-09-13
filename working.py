import time
from requests import Session
from concurrent.futures import as_completed, ProcessPoolExecutor
import enlighten
from collections import Counter
from requests_haor.core import RequestHaor

from requests.exceptions import Timeout, ConnectionError, ProxyError
from pydantic import BaseModel as Base
from pydantic import parse_obj_as as object_parser
from loguru import logger
from pprint import pprint
from datetime import datetime

from multiprocessing import cpu_count
from typing import List


logger.remove(0)
# logger.add(sys.stdout, colorize=True, format="{time} {level} {message}", level="INFO")


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


url = "https://finance.yahoo.com/quote/TSLA/financials?p=TSLA"
url = "http://jsonip.com/"
url = "https://www.bitmex.com/api/v1/chat?count=100&reverse=true"

REQUESTS_TO_SEND = 100

cpus = cpu_count() - 2
proxy_count = cpus * 2

# cpus = 4
# proxy_count = 2
#
# ###################################################################################################
# DESCRIPTION = "VANILLA REQUESTS SESSION + ProcessPoolExecutor TRYING NOT BACKING DOWN"
# start = time.time()
#
# results = []
# with ProcessPoolExecutor(max_workers=cpus) as executor:
#     session = Session()
#     futures = [
#         executor.submit(get_and_retry_recursively, url, session) for n in range(REQUESTS_TO_SEND)
#     ]
#
#     pbar = enlighten.Counter(total=REQUESTS_TO_SEND, desc=DESCRIPTION, unit="resp")
#     for future in as_completed(futures):
#         results.append(future.result())
#         pbar.update()
#
# end = time.time()
#
# print("took:", (end - start) / 60)
# print(Counter(results))
#
###################################################################################################
DESCRIPTION = "REQUESTOR SESSION + ProcessPoolExecutor NOT BACKING DOWN"

while True:
    print("ROUND AND ROUND WE GO!")

    start = time.time()

    results = []
    with RequestHaor(proxy_count=proxy_count) as session:
        with ProcessPoolExecutor(max_workers=cpus) as executor:

            futures = [
                executor.submit(get_and_retry_recursively, url, session)
                for n in range(REQUESTS_TO_SEND)
            ]

            pbar = enlighten.Counter(total=REQUESTS_TO_SEND, desc=DESCRIPTION, unit="resp")

            for future in as_completed(futures, timeout=120):
                results.append(future.result())
                pbar.update()

    end = time.time()

    print("took:", (end - start) / 60)
    print(Counter(results))

    print("sleep(15)")
    time.sleep(15)
