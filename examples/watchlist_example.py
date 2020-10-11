from concurrent.futures import as_completed, ThreadPoolExecutor

from nitter_scraper import NitterScraper
import pandas
from requests_whaor import RequestsWhaor
from yfs import fuzzy_search, get_options_page

watchlist = []
# Lets scrape the first page of eWhispers twitter feed for a list of symbols.
with NitterScraper(port=8008) as nitter:
    for tweet in nitter.get_tweets("eWhispers", pages=1):

        if tweet.is_pinned:  # Lets skip the pinned tweet.
            continue

        if tweet.is_retweet:  # Lets skip any retweets.
            continue

        if tweet.entries.cashtags:
            # Lets check if cashtags exists in the tweet then add them to the watchlist.
            watchlist += tweet.entries.cashtags

        print(".", end="", flush=True)  # Quick little progress_bar so we don't get bored.
    print()  # Print new line when complete just to make things look a little cleaner.


watchlist = sorted(set(map(lambda cashtag: cashtag.replace("$", "").strip(), watchlist)))
# Lets sort, remove duplicates, and clean '$' strings from each symbols.

valid_symbols = []  # Used to store symbols validated with the fuzzy_search function.
call_chains = []  # Used to store all the found call option chains.

# Decide on how many threads and proxies your computer can handle
MAX_THREADS = 6
# Each proxy is a tor circuit running inside a separate docker container.
MAX_PROXIES = 6

with RequestsWhaor(onion_count=MAX_PROXIES, max_threads=MAX_THREADS) as request_whaor:
    # RequestsWhaor will spin up a network of TOR nodes we will use as a rotating proxy.

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [
            executor.submit(
                fuzzy_search, ticker, session=request_whaor
            )  # ^--Here we pass request_whaor as a session like object.
            for ticker in watchlist
        ]

        for future in as_completed(futures):
            result = future.result(timeout=60)

            print(".", end="", flush=True)  # Quick progress bar.

            if result:
                # Now we append the results to the valid_symbols list.
                valid_symbols.append(result)

        # Lets get the raw symbol from each ValidSymbol object.
        valid_symbols = [ticker.symbol for ticker in valid_symbols]

        print("found", len(valid_symbols))  # Number of valid symbols found.

        request_whaor.restart_onions()  # Lets get a fresh pool of proxies before the next step.

        futures = [
            executor.submit(
                get_options_page,
                ticker,
                after_days=60,  # Lets get options that have at least 60 days before expiring.
                first_chain=True,  # We only want the first expiration with all strike prices.
                use_fuzzy_search=False,  # We did fuzzy search already no need to do it again.
                session=request_whaor,  # pass request_whaor as a session like object.
                page_not_found_ok=True,  # return None if the symbol doesn't have an option page.
                timeout=5,  # Pass a 5 second timeout to the session.
            )
            for ticker in valid_symbols
        ]

        for future in as_completed(futures):

            try:
                result = future.result(timeout=120)
                print(".", end="", flush=True)  # Progress bar.

                if result:
                    if result.calls:
                        # If the results have a call option chain we will append it to the list.
                        call_chains.append(result.calls)

            except Exception as exc:
                # We will pass on any exceptions.
                print(exc)

first_otm_strike = []

for chain in call_chains:
    df = chain.dataframe
    otm = df[df["in_the_money"] == False].head(1)

    if otm is not None:
        first_otm_strike.append(otm)

final = pandas.concat(first_otm_strike, ignore_index=True)
final.drop(columns=["timestamp", "contract_name"], inplace=True)
final.sort_values(by="implied_volatility", inplace=True)
final.reset_index(inplace=True)
print(final.to_string())
