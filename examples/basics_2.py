# title: Example of making 30 requests while getting a fresh pool of ip addresses every 10 requests.

from requests_whaor import RequestsWhaor

URL = "http://jsonip.com/"

with RequestsWhaor(onion_count=5) as requests_whaor:
    for _ in range(3):
        for _ in range(10):
            resp = requests_whaor.get(URL)

            if resp:
                print(resp.text)

        requests_whaor.restart_onions()
