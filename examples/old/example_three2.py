from requests_whaor import RequestsWhaor
import requests
from requests.exceptions import ProxyError, Timeout, ConnectionError
from concurrent.futures import as_completed, ProcessPoolExecutor, ThreadPoolExecutor
from collections import Counter
import time

URL = "https://www.bitmex.com/api/v1/chat?count=1&reverse=true"

REQUESTS_TO_SEND = 50
WORKERS = 5
PROXY_COUNT = WORKERS * 2

with RequestsWhaor(onion_count=PROXY_COUNT) as requests_whaor:
    while True:
        results = []
        message = ""
        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            futures = [executor.submit(requests_whaor.get, URL) for _ in range(REQUESTS_TO_SEND)]
            for future in as_completed(futures):
                result = future.result()

                if result.ok:
                    print(result.text)
                    results.append("PASSED")
                else:
                    print("FAILED!")
                    print(result)
                    print(result.text)
                    results.append("FAILED")

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
