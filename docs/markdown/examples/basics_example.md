# **Basic Usage**
## How to start a whaor network and make some requests.

```python

from requests_whaor import RequestsWhaor

URL = "http://jsonip.com/"

with RequestsWhaor(onion_count=5) as requests_whaor:
    for _ in range(10):
        resp = requests_whaor.get(URL)

        if resp:
            print(resp.text)

```


## Example of passing the rotating_proxy to a session object.

```python

from requests_whaor import RequestsWhaor
from requests.sessions import Session

URL = "http://jsonip.com/"

session = Session()
with RequestsWhaor(onion_count=5) as requests_whaor:
    for _ in range(10):
        result = session.get(URL, proxies=requests_whaor.rotating_proxy)
        print(result.text)

```


## Example of making 30 requests while getting a fresh pool of ip addresses every 10 requests.

```python

from requests_whaor import RequestsWhaor

URL = "http://jsonip.com/"

with RequestsWhaor(onion_count=5) as requests_whaor:
    for _ in range(3):
        for _ in range(10):
            resp = requests_whaor.get(URL)

            if resp:
                print(resp.text)

        requests_whaor.restart_onions()

```



