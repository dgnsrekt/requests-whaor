from requests_whaor import RequestsWhaor
import requests

URL = "http://jsonip.com/"

with RequestsWhaor(onion_count=5) as requests_whaor:
    for _ in range(10):
        result = requests.get(URL, proxies=requests_whaor.rotating_proxy)
        print(result.text)


from requests_whaor import RequestsWhaor

URL = "http://jsonip.com/"

with RequestsWhaor(onion_count=5, max_retries=10) as requests_whaor:
    for _ in range(10):
        result = requests_whaor.get(URL)
        print(result.text)
