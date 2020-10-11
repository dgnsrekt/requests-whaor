from yfs import get_summary_page, get_multiple_summary_pages
from requests_whaor import RequestsWhaor

with RequestsWhaor(onion_count=3, max_retries=10) as requests_whaor:
    while True:
        x = get_multiple_summary_pages(
            ["TSLA", "AAPL", "MICROSOFT", "FCEL", "GOOGLE", "SPY"],
            session=requests_whaor,
            with_threads=True,
            thread_count=6,
        )
        print(x.dataframe)
