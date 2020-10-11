# title: How to start a whaor network and make some requests.

from requests_whaor import RequestsWhaor

URL = "http://jsonip.com/"

with RequestsWhaor(onion_count=5) as requests_whaor:
    for _ in range(10):
        resp = requests_whaor.get(URL)

        if resp:
            print(resp.text)
