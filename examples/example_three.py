from requests_whaor import RequestsWhaor
import requests
from requests.exceptions import ProxyError, Timeout, ConnectionError
from concurrent.futures import as_completed, ProcessPoolExecutor
from collections import Counter

URL = "http://jsonip.com/"

REQUESTS_TO_SEND = 50
PROXY_COUNT = 10
WORKERS = 10


def get_retry_recursively(url, proxies, retry=5):
    try:
        response = requests.get(url, proxies=proxies, timeout=5)

        if response.ok:
            print(response.text)
            return "PASSED"

    except (ProxyError, Timeout, ConnectionError) as e:
        print()
        print(e)
        print(f"Will retry ({retry}) more times.")
        print()

    if retry > 0:
        retry -= 1
    else:
        return "FAILED"

    return get_retry_recursively(url, proxies, retry=retry)


results = []
with RequestsWhaor(proxy_count=PROXY_COUNT) as requests_whaor:
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        futures = [
            executor.submit(get_retry_recursively, URL, requests_whaor.rotating_proxy)
            for _ in range(REQUESTS_TO_SEND)
        ]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
        else:
            print("done.")

print(Counter(results))
