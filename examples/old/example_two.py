from requests_whaor import RequestsWhaor
import requests
from requests.sessions import Session
from requests.exceptions import ProxyError, Timeout, ConnectionError

URL = "http://jsonip.com/"


def get_retry_loop(url, proxies, retry=5):
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

    return get_retry_loop(url, proxies, retry=retry)


session = Session()

with RequestsWhaor(onion_count=5) as requests_whaor:
    for _ in range(10):
        result = session.get(URL, proxies=requests_whaor.rotating_proxy)
        print(result)
