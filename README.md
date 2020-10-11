# **requests-whaor** [[ri-kwests](https://www.dictionary.com/browse/requests) [hawr](https://www.dictionary.com/browse/whore)]

[**Requests**](https://requests.readthedocs.io) **+** [**Docker**](https://www.docker.com/) **+** [**HAproxy**](http://www.haproxy.org/) **+** [**Tor**](https://www.torproject.org/)

**Requests** **W**ith **H**igh **A**vailability **O**nion **R**outer. For the filthiest web scrapers that have no time for rate-limits.

[![Black](https://img.shields.io/badge/code%20style-black-black?style=for-the-badge&logo=appveyor)](https://github.com/psf/black)
[![GitHub](https://img.shields.io/github/license/dgnsrekt/requests-whaor?style=for-the-badge)](https://raw.githubusercontent.com/dgnsrekt/requests-whaor/master/LICENSE)


## Overview
**requests-whaor** proxies GET requests through a local **Docker** network of **TOR** circuits. It takes care of starting and stopping a pool of **TOR** proxies behind an **HAproxy** load balancer, which acts as a round robin reverse proxy network. This will give each request a new IP address.  If you start having issues with the initial pool of IPs, **requests-whaor** can gather a new pool of IP addresses by restarting all **TOR** containers.

## Install with pip
```
pip install requests-whaor
```

## Install with [Poetry](https://python-poetry.org/)
```
poetry add requests-whaor
```


## [>> **Quickstart** / **Docs** <<](https://dgnsrekt.github.io/requests-whaor/quickstart)

## Projects to highlight.
* [**dperson's**](https://hub.docker.com/u/dperson) - [torproxy docker container](https://hub.docker.com/r/dperson/torproxy)
* [**zet4's**](https://github.com/zet4) - [alpine-tor library](https://github.com/zet4/alpine-tor)
* [torproject](https://www.torproject.org/)
* [haproxy](https://hub.docker.com/_/haproxy)

## Useful Docker commands.
### If things get out of hand you may need these commands for debugging or killing containers.
```
docker ps -q --filter ancestor=osminogin/tor-simple | xargs -L 1 docker logs --follow

docker ps -q --filter ancestor=osminogin/haproxy | xargs -L 1 docker logs --follow

docker stop $(docker ps -q --filter ancestor=osminogin/tor-simple)

docker stop $(docker ps -q --filter ancestor=haproxy)

docker network rm $(docker network ls -q -f name=whaornet)
```

## TODO
* [ ] Testing.
* [ ] More request methods if requested.
* [ ] Options for using different Tor containers.
* [ ] Options for different load balancer containers.

## Contact Information
Telegram = Twitter = Tradingview = Discord = @dgnsrekt

Email = dgnsrekt@pm.me
