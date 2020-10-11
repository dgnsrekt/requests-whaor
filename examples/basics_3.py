# title: Example of passing the rotating_proxy to a session object.

from requests_whaor import RequestsWhaor
from requests.sessions import Session

URL = "http://jsonip.com/"

session = Session()
with RequestsWhaor(onion_count=5) as requests_whaor:
    for _ in range(10):
        result = session.get(URL, proxies=requests_whaor.rotating_proxy)
        print(result.text)
