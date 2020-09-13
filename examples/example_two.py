from requests_haor import RequestHaor
import requests
from requests.exceptions import ProxyError, Timeout, ConnectionError

URL = "http://jsonip.com/"


def get_retry_recursively(url, proxies, retry=5):
    try:
        response = requests.get(url, proxies=proxies, timeout=5)

        if response.ok:
            print(response.text)
            return "PASSED"

    except (ProxyError, Timeout, ConnectionError) as e:
        print(e)
        print(f"Will retry ({retry}) more times.")

    if retry > 0:
        retry -= 1
    else:
        return "FAILED"

    return get_retry_recursively(url, proxies, retry=retry)


with RequestHaor(proxy_count=5) as requests_haor:
    for _ in range(10):
        result = get_retry_recursively(URL, requests_haor.rotating_proxy)
        print(result)
