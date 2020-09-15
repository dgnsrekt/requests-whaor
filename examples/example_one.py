from requests_whaor import RequestsWhaor
import requests

URL = "http://jsonip.com/"

with RequestsWhaor(proxy_count=5) as requests_whaor:
    for _ in range(10):
        try:
            resp = requests_whaor.get(URL)

            if resp.ok:
                print(resp.text)

        except Exception as e:
            print(e)
