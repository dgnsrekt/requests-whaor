# How to build a one delta OTM call options watchlist from twitter cashtags.

## Overview
1. First, we will scrape a users tweets for cashtags with [nitter_scraper](https://github.com/dgnsrekt/nitter_scraper/)
2. Next, we will prepare and clean the tweet data to build a watchlist.
3. After that, we will startup a network of tor nodes behind a reverse proxy, to bypass the yahoo finance rate limit, using [requests-whaor](https://github.com/dgnsrekt/requests-whaor/)
4. Last, we will download, clean, and concatenate all the options data into a single DataFrame.

## Requirements
* [Docker Engine](https://docs.docker.com/engine/) installed.
* python ^3.8
* [poetry](https://python-poetry.org/)

## Dependencies
* [yfs](https://github.com/dgnsrekt/yfs/)
* [nitter_scraper](https://github.com/dgnsrekt/nitter_scraper/)
* [requests-whaor](https://github.com/dgnsrekt/requests-whaor/)

!!! note
    requests-whaor will create multiple TOR nodes enclosed in docker containers to proxy your requests.

## Environment Preparation
Run the following commands to build a folder and initiate a poetry project.

```bash
$ mkdir yfs_watchlist
$ cd yfs_watchlist
$ poetry init
```
Keep hitting the enter button until you are out of the poetry init prompt.

Now lets add the dependencies.

```bash
$ poetry add nitter-scraper
$ poetry add requests-whaor
$ poetry add yfs

```

Create options_bot.py

```bash
$ touch options_bot.py
```
Open options_bot.py in your favorite editor.

## Imports

```python
from concurrent.futures import as_completed, ThreadPoolExecutor
```
The ThreadPoolExecutor is used to call fuzzy_search and get_options_page functions asynchronously with a pool of threads.

```python
from nitter_scraper import NitterScraper
```
The nitter_scraper library is used to scrape tweets.

```python
import pandas
```
The pandas library is used to clean and concatenate the DataFrames.

```python
from requests_whaor import RequestsWhaor
```
The requests_whaor library will supply a rotating proxy server to send our requests through, giving each request a unique IP address. If a request times out or gets a error code from the server it will retry with another IP address.

```python
from yfs import fuzzy_search, get_options_page
```
Last we use these yfs functions to search for valid symbols and get options data.


```python
from concurrent.futures import as_completed, ThreadPoolExecutor

from nitter_scraper import NitterScraper
import pandas
from requests_whaor import RequestsWhaor
from yfs import fuzzy_search, get_options_page
```

The imports should look like this.


## Scrape Twitter and build a watchlist

```python

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

        print(".", end="", flush=True)  # Quick little progress bar so we don't get bored.
    print()  # Print a new line when complete just to make things look a little cleaner.


watchlist = sorted(set(map(lambda cashtag: cashtag.replace("$", "").strip(), watchlist)))
# Lets sort, remove duplicates, and clean '$' strings from each symbol.
```

Now we have a dynamically generated list of potentially interesting stock symbols.


```python
valid_symbols = [] # Used to store symbols validated with the fuzzy_search function.
call_chains = [] # Used to store all the found call option chains.

# Decide on how many threads and proxies your computer can handle
MAX_THREADS = 6
# Each proxy is a tor circuit running inside a separate docker container.
MAX_PROXIES = 6
```

Now on to the meat of the code.

```python
with RequestsWhaor(onion_count=MAX_PROXIES, max_threads=MAX_THREADS) as request_whaor:
    # RequestsWhaor will spin up a network of TOR nodes we will use as a rotating proxy.

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [
            executor.submit(
                fuzzy_search, ticker, session=request_whaor
            )  # ^--Here we pass request_whaor as a session like object for yfs fuzzy_search.
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
                session=request_whaor,  # pass request_whaor as a session like object to yfs.
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

```

!!! note
    [ThreadPoolExecutor information here.](https://docs.python.org/3/library/concurrent.futures.html)


## Final Section

* First, iterate over the result.
* Then, convert each chain into a dataframe.
* Next, get the first out of the money option and append it to a list.
* After that, concatenate the list of single option contract dataframes into a single dataframe.
* Now lets, drop some columns and sort by implied volatility to make things look pretty.
* Finally, print the results.

```python
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
```

Now we have a single dataframe of one delta OTM call options built from a dynamically generated watch list.

??? success "Output"
    ```bash

    index symbol contract_type           expiration_date  in_the_money  strike  last_price    bid    ask  change percent_change volume  open_interest  implied_volatility
    0      122    SNX          call 2020-12-18 00:00:00+00:00         False   155.0        5.92   0.00   0.00    0.00            NaN      7           19.0                1.56
    1       10    AZZ          call 2021-02-19 00:00:00+00:00         False    40.0        2.00   0.00   0.00    0.00           None      1            0.0                3.13
    2      133   USAT          call 2021-01-15 00:00:00+00:00         False    10.0        1.25   0.00   0.00    0.00           None      2           41.0               12.50
    3      116   SINA          call 2020-12-18 00:00:00+00:00         False    45.0        0.05   0.05   0.50    0.00            NaN      5           59.0               18.36
    4       71    JNJ          call 2020-12-18 00:00:00+00:00         False   155.0        3.75   3.70   3.80    0.55          17.19    150         3168.0               21.05
    5       94    PEP          call 2020-12-18 00:00:00+00:00         False   140.0        4.26   4.15   4.45    0.10            2.4     38         4826.0               21.51
    6       31   COST          call 2021-01-15 00:00:00+00:00         False   370.0       18.60  18.50  18.95    1.46           8.52     90         1326.0               25.29
    7       55    GIS          call 2021-01-15 00:00:00+00:00         False    62.5        2.99   2.57   2.99    0.39             15      7         1501.0               25.78
    8       59   INFO          call 2020-12-18 00:00:00+00:00         False    80.0        3.46   2.65   3.10    0.00           None      1          314.0               27.06
    9       95    PGR          call 2021-01-15 00:00:00+00:00         False   100.0        5.15   5.00   5.60    0.65          14.44     29          613.0               27.55
    10      81    MKC          call 2020-12-18 00:00:00+00:00         False   200.0        7.50   7.10   7.70    0.50           7.14      6          188.0               27.72
    11       0    ACN          call 2021-01-15 00:00:00+00:00         False   230.0       12.50  12.40  13.20    1.50          13.64     63          596.0               29.38
    12      27    CAG          call 2020-12-18 00:00:00+00:00         False    38.0        1.54   1.40   1.60   -0.06          -3.75      2          523.0               29.42
    13      97   PAYX          call 2020-12-18 00:00:00+00:00         False    82.5        3.80   3.80   4.20    0.00            NaN      4         1391.0               29.74
    14      93   ORCL          call 2020-12-18 00:00:00+00:00         False    62.5        2.53   2.47   2.60    0.08           3.27     27         9815.0               30.14
    15     139   WABC          call 2021-01-15 00:00:00+00:00         False    65.0        0.80   0.75   1.05    0.00           None      2           22.0               30.74
    16      22    BLK          call 2021-01-15 00:00:00+00:00         False   620.0       32.10  28.00  36.20    1.75           5.77     46          140.0               31.83
    17      88    NKE          call 2021-01-15 00:00:00+00:00         False   135.0        6.85   6.70   6.85    0.35           5.38     92         2130.0               31.89
    18      74    KSU          call 2020-12-18 00:00:00+00:00         False   190.0        8.40   6.20   9.00    0.78          10.24      1           57.0               32.46
    19      21     BK          call 2020-12-18 00:00:00+00:00         False    40.0        1.20   1.10   1.25    0.15          14.29    150         2705.0               32.86
    20      50    FRC          call 2021-02-19 00:00:00+00:00         False   125.0        1.66   8.40   9.20    0.00            NaN      1            4.0               32.98
    21     144    WNS          call 2021-01-15 00:00:00+00:00         False    75.0        1.15   1.45   1.90    0.00           None     48          103.0               33.03
    22      41    DPZ          call 2020-12-18 00:00:00+00:00         False   400.0       18.00  15.00  18.90   -7.10         -28.29    147          265.0               33.77
    23      28   CASY          call 2021-02-19 00:00:00+00:00         False   185.0       10.90  10.50  14.20    0.00           None    NaN            8.0               34.07
    24     102    PNC          call 2021-01-15 00:00:00+00:00         False   120.0        6.30   5.70   6.20   -0.60           -8.7     21          451.0               34.17
    25     111    RPM          call 2021-02-19 00:00:00+00:00         False    90.0        5.40   4.00   6.00    0.00            NaN      2          178.0               34.38
    26      47    FDS          call 2020-12-18 00:00:00+00:00         False   330.0       16.01  14.50  18.50    0.00           None      1           38.0               34.64
    27      61   JBHT          call 2021-01-15 00:00:00+00:00         False   140.0        6.50   6.20   7.60   -0.40           -5.8      2           51.0               34.69
    28      52     GS          call 2021-01-15 00:00:00+00:00         False   210.0       13.50  13.40  13.70   -0.89          -6.18    236         3466.0               34.74
    29      44   FAST          call 2021-01-15 00:00:00+00:00         False    47.5        2.75   2.60   2.95    0.10           3.77      5          293.0               34.83
    30     135    UNH          call 2020-12-18 00:00:00+00:00         False   330.0       17.84  15.75  18.80    3.24          22.19    100         1289.0               34.84
    31     121    STZ          call 2021-01-15 00:00:00+00:00         False   190.0       10.30  10.10  11.90    0.50            5.1     41          744.0               34.92
    32      19    AZO          call 2020-12-18 00:00:00+00:00         False  1140.0       72.00  60.90  68.50    0.00            NaN      1            5.0               35.27
    33     101   PRGS          call 2020-12-18 00:00:00+00:00         False    45.0        0.67   0.60   0.90    0.00            NaN      6          399.0               35.60
    34      69    JPM          call 2020-12-18 00:00:00+00:00         False   105.0        4.55   4.50   4.65   -0.63         -12.16    280        12567.0               35.66
    35      65   INFY          call 2021-01-15 00:00:00+00:00         False    16.0        0.75   0.70   0.80    0.15             25     31          328.0               36.08
    36      84     MS          call 2020-12-18 00:00:00+00:00         False    50.0        2.52   2.53   2.58   -0.21          -7.69   2415         1027.0               36.55
    37      39   CTAS          call 2020-12-18 00:00:00+00:00         False   340.0       19.75  17.10  21.50    0.00            NaN      2           14.0               36.91
    38      54    HDS          call 2020-12-18 00:00:00+00:00         False    45.0        1.80   1.65   1.90    0.20           12.5      3          176.0               37.23
    39      13    BAC          call 2020-12-18 00:00:00+00:00         False    26.0        1.31   1.31   1.37   -0.05          -3.68    937        20691.0               37.55
    40      33   CALM          call 2020-12-18 00:00:00+00:00         False    40.0        1.50   1.40   1.70   -0.40         -21.05     20           49.0               38.09
    41       7   ASML          call 2021-01-15 00:00:00+00:00         False   390.0       28.40  27.40  30.00    4.50          18.83      3          479.0               38.13
    42     114   SCHW          call 2020-12-18 00:00:00+00:00         False    39.0        1.89   1.98   2.19   -0.01          -0.53     39          373.0               38.21
    43      16      C          call 2020-12-18 00:00:00+00:00         False    45.0        2.95   2.91   2.97   -0.10          -3.28    165        10174.0               38.57
    44      60   ISRG          call 2020-12-18 00:00:00+00:00         False   740.0       48.00  43.70  50.40   13.60          39.53      5          217.0               40.06
    45     129    TFC          call 2020-12-18 00:00:00+00:00         False    45.0        1.97   1.95   2.25   -0.09          -4.37      2         3577.0               40.09
    46      56   HELE          call 2020-12-18 00:00:00+00:00         False   200.0        7.93   9.80  12.90    0.00            NaN      2           12.0               40.09
    47      75   LNDC          call 2020-12-18 00:00:00+00:00         False    12.5        0.10   0.05   0.10   -0.05         -33.33      1           56.0               40.23
    48     137    VFC          call 2021-01-15 00:00:00+00:00         False    80.0        4.80   4.90   5.40    0.00            NaN      7          160.0               40.33
    49      79     LW          call 2021-01-15 00:00:00+00:00         False    75.0        5.40   4.80   5.30   -0.60            -10      1          251.0               40.44
    50     123    STT          call 2021-01-15 00:00:00+00:00         False    67.5        4.70   4.70   5.10    1.80          62.07      2          145.0               40.87
    51     134    USB          call 2020-12-18 00:00:00+00:00         False    40.0        2.42   2.19   2.41   -0.19          -7.28     59         3619.0               40.92
    52       1    ABM          call 2021-01-15 00:00:00+00:00         False    40.0        2.11   1.60   2.00    0.00           None      1           90.0               41.53
    53      48    FDX          call 2021-01-15 00:00:00+00:00         False   280.0       19.34  18.95  19.55   -0.96          -4.73    152         2159.0               41.57
    54       9    AYI          call 2020-12-18 00:00:00+00:00         False   100.0        7.90   5.80   7.10   -8.45         -51.68    125           24.0               42.15
    55      36    CMC          call 2020-12-18 00:00:00+00:00         False    23.0        1.50   1.35   1.50    0.10           7.14     24         1212.0               42.33
    56     107    RGP          call 2021-02-19 00:00:00+00:00         False    12.5        0.75   0.65   0.85    0.75           None     56          347.0               42.53
    57       8   ADBE          call 2020-12-18 00:00:00+00:00         False   505.0       33.63  34.30  35.90    3.82          12.81     30         1044.0               42.76
    58     125   TCOM          call 2020-12-18 00:00:00+00:00         False    33.0        2.10   1.80   2.03    0.00            NaN     54         2102.0               42.92
    59     142    WFC          call 2020-12-18 00:00:00+00:00         False    27.5        1.02   1.01   1.07   -0.04          -3.77    550        31241.0               43.31
    60     130    TSM          call 2020-12-18 00:00:00+00:00         False    90.0        6.15   6.00   6.20    0.45           7.89    406         1115.0               43.87
    61      82    MTN          call 2020-12-18 00:00:00+00:00         False   250.0        9.00  11.10  14.90    0.00            NaN      1           45.0               44.12
    62     138   VRNT          call 2020-12-18 00:00:00+00:00         False    55.0        2.80   2.95   3.30    0.30             12      2         3136.0               44.12
    63     141    WBA          call 2020-12-18 00:00:00+00:00         False    37.5        2.01   1.58   2.33   -0.18          -8.22      1          370.0               44.92
    64      42    EDU          call 2021-01-15 00:00:00+00:00         False   175.0        7.18  12.60  13.60    0.00            NaN      1           15.0               45.00
    65      72    LEN          call 2021-01-15 00:00:00+00:00         False    85.0        7.30   7.20   7.40   -0.20          -2.67     22          832.0               45.29
    66      66    JBL          call 2020-12-18 00:00:00+00:00         False    37.0        2.45   2.20   2.65    0.35          16.67      1           12.0               46.51
    67      43   EPAC          call 2021-02-19 00:00:00+00:00         False    20.0        1.55   1.25   2.05    0.00           None    153          289.0               46.63
    68      35   CVGW          call 2021-01-15 00:00:00+00:00         False    70.0        4.00   3.90   6.00    0.00           None    NaN            4.0               46.89
    69      68    KMX          call 2021-01-15 00:00:00+00:00         False    95.0        8.00   7.90   9.20   -0.90         -10.11     17          944.0               47.31
    70      85     MU          call 2020-12-18 00:00:00+00:00         False    50.0        4.00   4.00   4.10    4.00           None    444          994.0               48.05
    71      80   LULU          call 2020-12-18 00:00:00+00:00         False   350.0       26.80  26.80  27.25    3.35          14.29    123          480.0               48.07
    72      40    DRI          call 2021-01-15 00:00:00+00:00         False   105.0        8.80   8.20   8.80    0.44           5.26      3          857.0               48.21
    73      57   HOMB          call 2020-12-18 00:00:00+00:00         False    17.5        0.90   0.70   1.20    0.00           None     55          187.0               49.22
    74      11   APOG          call 2021-02-19 00:00:00+00:00         False    30.0        1.35   1.40   1.50    0.22          19.47      2          204.0               49.71
    75      73   LEVI          call 2021-01-15 00:00:00+00:00         False    16.0        1.20   1.20   1.25   -0.25         -17.24    100         1362.0               50.44
    76     140     WB          call 2021-01-15 00:00:00+00:00         False    45.0        2.88   2.55   3.10   -0.02          -0.69     16         1531.0               50.46
    77     143    WOR          call 2020-12-18 00:00:00+00:00         False    50.0        3.13   2.15   3.30    0.23           7.93      7          359.0               50.76
    78      67    KBH          call 2021-01-15 00:00:00+00:00         False    45.0        2.80   2.60   2.80    0.44          18.64     17          271.0               50.98
    79      26   ALLY          call 2020-12-18 00:00:00+00:00         False    28.0        2.57   2.20   2.59    0.15            6.2     35         1403.0               51.07
    80      99    PHR          call 2021-01-15 00:00:00+00:00         False    35.0        2.50   1.85   2.60    0.30          13.64      1           49.0               51.51
    81      17   AVAV          call 2020-12-18 00:00:00+00:00         False    75.0        5.00   4.40   5.20    0.71          16.55      4          104.0               51.79
    82      18     BB          call 2020-12-18 00:00:00+00:00         False     5.0        0.31   0.30   0.33    0.01           3.33     18         1416.0               51.95
    83      34    CMD          call 2020-12-18 00:00:00+00:00         False    50.0        2.65   2.75   3.70    0.00            NaN      3            3.0               52.47
    84      90   NEOG          call 2021-01-15 00:00:00+00:00         False    80.0        7.00   2.50   7.50    0.00           None      2           15.0               54.53
    85     146     ZS          call 2021-01-15 00:00:00+00:00         False   155.0       15.85  14.75  16.65    1.45          10.07    115         1113.0               54.60
    86     109   SCHL          call 2020-12-18 00:00:00+00:00         False    22.5        1.45   1.20   1.70    0.00            NaN      5           13.0               54.79
    87       6   ANGO          call 2021-01-15 00:00:00+00:00         False    12.5        1.02   0.70   1.25    0.00            NaN      3           36.0               55.47
    88      49    FUL          call 2021-02-19 00:00:00+00:00         False    50.0        4.20   2.75   6.30    0.00           None      1          126.0               55.47
    89      30   CBRL          call 2020-12-18 00:00:00+00:00         False   120.0        8.60   7.70  10.60    0.00           None      2          141.0               55.54
    90     120    SLB          call 2020-12-18 00:00:00+00:00         False    17.5        1.07   1.03   1.11    1.07           None      8           58.0               55.76
    91     147   ZUMZ          call 2021-02-19 00:00:00+00:00         False    35.0        2.66   2.65   3.00    0.00            NaN      2           37.0               56.10
    92      24   CAMP          call 2020-12-18 00:00:00+00:00         False    10.0        0.20   0.00   0.40    0.00           None     10          570.0               56.25
    93      98    OSH          call 2021-04-16 00:00:00+00:00         False    65.0        4.76   2.50   6.30    4.76           None    100          101.0               56.38
    94      64    HQY          call 2020-12-18 00:00:00+00:00         False    60.0        3.50   3.40   3.70    0.00            NaN      1          584.0               56.49
    95      32   COUP          call 2020-12-18 00:00:00+00:00         False   310.0       29.00  27.30  28.60    5.33          22.52      7           78.0               57.75
    96      77   LMNR          call 2020-12-18 00:00:00+00:00         False    15.0        1.25   1.05   1.95    0.00           None      2            2.0               58.20
    97     127    THO          call 2020-12-18 00:00:00+00:00         False    97.5        9.00   9.20   9.70   -6.20         -40.79     11           27.0               58.96
    98     110     RH          call 2021-01-15 00:00:00+00:00         False   380.0       44.15  41.60  43.30   -0.07          -0.16      8          412.0               60.54
    99      89     NG          call 2020-12-18 00:00:00+00:00         False    12.0        0.77   0.85   1.05    0.00            NaN     20         1163.0               60.64
    100     37   CMTL          call 2021-01-15 00:00:00+00:00         False    17.5        1.75   1.55   1.70    0.55          45.83      1          312.0               60.94
    101      5    AEO          call 2021-01-15 00:00:00+00:00         False    16.0        1.70   1.55   1.80   -0.20         -10.53     20          270.0               62.40
    102    112   SCWX          call 2021-01-15 00:00:00+00:00         False    12.5        1.00   1.15   1.30    0.00           None     61          148.0               62.70
    103    103   RFIL          call 2021-01-15 00:00:00+00:00         False     5.0        0.35   0.30   0.50    0.00           None      9          122.0               63.67
    104    148   WORK          call 2020-12-18 00:00:00+00:00         False    32.0        3.00   2.95   3.05    0.51          20.48    608         8478.0               63.84
    105      4     AA          call 2020-12-18 00:00:00+00:00         False    13.0        1.26   1.16   1.24    0.00            NaN      6          145.0               64.70
    106     29   CHWY          call 2021-01-15 00:00:00+00:00         False    65.0        6.90   6.80   6.95    1.31          23.43    449         3579.0               65.43
    107    119   SLQT          call 2021-01-15 00:00:00+00:00         False    20.0        2.40   2.35   2.60   -0.20          -7.69     12          361.0               65.63
    108     38    DAL          call 2020-12-18 00:00:00+00:00         False    33.0        3.65   3.55   3.80    0.00            NaN     19         1220.0               66.26
    109    126   SNBR          call 2020-12-18 00:00:00+00:00         False    60.0        3.50   4.20   5.10    0.00            NaN      5          129.0               66.75
    110    117    SGH          call 2020-12-18 00:00:00+00:00         False    30.0        1.00   0.50   2.25   -0.05          -4.76      1           79.0               68.07
    111    131   UEPS          call 2021-01-15 00:00:00+00:00         False     4.0        0.38   0.15   0.40    0.00           None     63          326.0               68.36
    112     87    NAV          call 2020-12-18 00:00:00+00:00         False    46.0        2.70   0.20   5.00    2.70           None      3            0.0               70.92
    113     86   NCNO          call 2021-02-19 00:00:00+00:00         False    80.0       13.54  13.00  13.90    0.84           6.61      8           52.0               71.03
    114    124   TACO          call 2020-12-18 00:00:00+00:00         False    10.0        0.94   0.80   1.05    0.09          10.59     14          893.0               71.09
    115    132   UNFI          call 2021-02-19 00:00:00+00:00         False    17.5        2.75   2.50   3.00    0.05           1.85     58          550.0               72.07
    116     78   MCFT          call 2021-01-15 00:00:00+00:00         False    20.0        2.95   2.55   3.40    0.00            NaN      1           16.0               72.75
    117    115   SFIX          call 2020-12-18 00:00:00+00:00         False    32.0        3.39   3.65   3.85   -0.20          -5.57     24          277.0               73.05
    118     62    HMY          call 2021-01-15 00:00:00+00:00         False     6.0        0.90   0.75   1.00    0.20          28.57     24         1835.0               73.24
    119    104   REVG          call 2021-01-15 00:00:00+00:00         False    10.0        0.50   0.45   1.20    0.00           None      5           43.0               73.44
    120    100   PTON          call 2021-01-15 00:00:00+00:00         False   125.0       19.00  17.50  19.00    3.87          25.58    198         1423.0               75.85
    121     14   BBBY          call 2020-12-18 00:00:00+00:00         False    22.0        2.67   2.59   2.69   -0.26          -8.87     12          549.0               77.34
    122    145   VITL          call 2021-01-15 00:00:00+00:00         False    40.0        7.00   5.30   6.90    0.00            NaN      3           10.0               77.73
    123    136    UAL          call 2020-12-18 00:00:00+00:00         False    38.0        4.70   4.60   4.70    0.40            9.3     42         1094.0               78.32
    124     12   APHA          call 2021-01-15 00:00:00+00:00         False     6.0        0.82   0.80   0.85   -0.07          -7.87    150         5032.0               78.71
    125     70   LAKE          call 2021-01-15 00:00:00+00:00         False    25.0        2.85   2.75   3.10    0.60          26.67     68          972.0               79.88
    126    128    TNP          call 2020-12-18 00:00:00+00:00         False    10.0        0.50   0.45   0.60   -0.13         -20.63     61          267.0               80.47
    127    105    RAD          call 2021-01-15 00:00:00+00:00         False    11.0        1.30   1.09   1.53   -0.09          -6.47     45          367.0               80.76
    128     45    EPM          call 2021-01-15 00:00:00+00:00         False     2.5        0.30   0.05   0.50    0.10             50      2           71.0               85.16
    129     23    BRC          call 2021-05-21 00:00:00+00:00         False    45.0        3.40   0.20  10.00    0.00           None   None           32.0               86.30
    130     51   GIII          call 2020-12-18 00:00:00+00:00         False    17.5        1.45   1.45   1.70    0.00            NaN      9          492.0               87.74
    131     25    CCL          call 2021-01-15 00:00:00+00:00         False    17.5        2.21   2.10   2.21    0.09           4.25   7323        25364.0               87.94
    132     46    FLR          call 2021-01-15 00:00:00+00:00         False    12.5        1.46   1.35   1.50   -0.03          -2.01    327         4591.0               89.06
    133     76   LOVE          call 2021-01-15 00:00:00+00:00         False    35.0        6.17   5.40   6.20    1.17           23.4      8           72.0               89.40
    134      3   AGTC          call 2021-01-15 00:00:00+00:00         False     7.5        0.50   0.35   0.65    0.00           None     11         2942.0               93.95
    135     91   MRTN          call 2020-12-18 00:00:00+00:00         False    17.5        1.75   0.00   2.90    0.00           None    NaN            2.0               98.39
    136     63    JKS          call 2020-12-18 00:00:00+00:00         False    65.0       10.00   8.70  11.00    3.80          61.29    120          277.0               99.05
    137     96   PLAY          call 2021-01-15 00:00:00+00:00         False    17.5        2.85   2.65   2.90    0.05           1.79    106         1772.0              100.44
    138     20   BIGC          call 2021-01-15 00:00:00+00:00         False   100.0       19.24  19.00  19.35    2.88           17.6     70         1036.0              100.83
    139     92   NTWK          call 2021-01-15 00:00:00+00:00         False     5.0        0.10   0.00   0.30    0.00            NaN      5           68.0              103.52
    140    108   RLGT          call 2020-12-18 00:00:00+00:00         False     7.5        0.10   0.00   0.80    0.00           None      2           17.0              112.50
    141     58   ICMB          call 2021-01-15 00:00:00+00:00         False     5.0        0.20   0.00   0.50    0.00           None     30          126.0              117.19
    142    113   SANW          call 2021-02-19 00:00:00+00:00         False     2.5        1.11   0.00   1.25    0.00           None     12            6.0              122.66
    143      2    ACB          call 2020-12-18 00:00:00+00:00         False     6.0        0.75   0.62   0.88    0.00            NaN    255         1199.0              124.22
    144     83   MEIP          call 2020-12-18 00:00:00+00:00         False     5.0        0.20   0.20   0.25    0.00           None      6        12699.0              127.73
    145    106    QTT          call 2021-01-15 00:00:00+00:00         False     5.0        0.25   0.10   0.35    0.10          66.67      3          285.0              132.42
    146     53    GME          call 2020-12-18 00:00:00+00:00         False    13.0        2.49   2.45   2.76    2.49           None    101           27.0              143.85
    147    118   SEAC          call 2021-01-15 00:00:00+00:00         False     2.5        0.05   0.00   0.15    0.00           None      1         1805.0              169.53
    148     15   BCLI          call 2020-12-18 00:00:00+00:00         False    20.0        7.00   6.60   7.50    0.04           0.57     37          764.0              266.89

    ```

## Full Script

```python
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
```
