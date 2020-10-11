from requests_whaor import RequestsWhaor
import requests
from requests.exceptions import ProxyError, Timeout, ConnectionError
from concurrent.futures import as_completed, ProcessPoolExecutor
from collections import Counter
import time

URL = "https://www.bitmex.com/api/v1/chat?count=1&reverse=true"

REQUESTS_TO_SEND = 50
WORKERS = 5
PROXY_COUNT = WORKERS * 2


def get_retry_loop(url, proxies, retry=5):
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

    return get_retry_loop(url, proxies, retry=retry)


with RequestsWhaor(onion_count=PROXY_COUNT) as requests_whaor:
    while True:
        results = []
        message = ""
        with ProcessPoolExecutor(max_workers=WORKERS) as executor:
            futures = [
                executor.submit(get_retry_loop, URL, requests_whaor.rotating_proxy)
                for _ in range(REQUESTS_TO_SEND)
            ]
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
            else:
                print("done.")

        pass_count = Counter(results)

        print(pass_count)
        time.sleep(2.5)

        if pass_count["PASSED"] < 50:
            print("done")
            break
        else:
            print("still going strong.")

        requests_whaor.restart_onions()
        requests_whaor.onion_balancer.display_settings()
