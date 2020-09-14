from requests_haor import RequestsHaor
import requests
from requests.exceptions import ProxyError, Timeout, ConnectionError
from concurrent.futures import as_completed, ProcessPoolExecutor
from collections import Counter
from pydantic import BaseModel as Base
from typing import List
from datetime import datetime


class Mexssage(Base):
    id: int
    date: datetime
    user: str
    message: str
    channelID: int
    fromBot: bool


URL = "https://www.bitmex.com/api/v1/chat?count=1&reverse=true"

PROXY_COUNT = 10


def get_retry_recursively(url, proxies, retry=5):
    try:
        response = requests.get(url, proxies=proxies, timeout=5)

        if response.ok:
            return Mexssage(**response.json()[0])

    except (ProxyError, Timeout, ConnectionError) as e:
        print()
        print(e)
        print(f"Will retry ({retry}) more times.")
        print()

    if retry > 0:
        retry -= 1
    else:
        return None

    return get_retry_recursively(url, proxies, retry=retry)


last_mexssage_id = None
with RequestsHaor(proxy_count=PROXY_COUNT) as requests_haor:
    while True:
        mexssage = get_retry_recursively(URL, requests_haor.rotating_proxy)

        # if mexssage.channelID != 1:
        # continue

        if mexssage.id == last_mexssage_id:
            continue

        else:
            last_mexssage_id = mexssage.id
            print(mexssage.json(indent=4))
