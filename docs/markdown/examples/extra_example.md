# **Extra Examples**
## Poll bitmex chat example.

```python

from datetime import datetime
from typing import List

from requests_whaor import RequestsWhaor
from pydantic import BaseModel as Base
from pydantic import Field


class Mexssage(Base):
    id: int
    date: datetime
    user: str
    message: str
    channel: int = Field(alias="channelID")
    from_bot: bool = Field(alias="fromBot")


class MexssageList(Base):
    message_list: List[Mexssage]

    def __iter__(self):
        return iter(self.message_list)


URL = "https://www.bitmex.com/api/v1/chat?count=50&reverse=true"

PROXY_COUNT = 10

last_mexssage = None
request_count = 1

print("Websockets?! Where we're going We don't need Websockets!!!")

with RequestsWhaor(onion_count=PROXY_COUNT) as requests_whaor:
    while True:
        resp = requests_whaor.get(URL)
        request_count += 1

        mexssage = MexssageList(message_list=resp.json())

        for msg in mexssage:
            if last_mexssage is None:
                last_mexssage = msg.id

            if msg.id > last_mexssage:
                last_mexssage = msg.id
                print(msg.json(indent=4))

        if request_count % 100 == 0:
            requests_whaor.restart_onions()


```

!!! note
    You should use websockets for this.


