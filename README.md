# requests-haor

# Requests with a High Availability Onion Rotator
requests + docker + haproxy + tor

For the web scraper that needs data now and has no time for rate-limits.

You may need this.
```
docker stop $(docker ps -q --filter ancestor=osminogin/tor-simple:latest)
docker stop $(docker ps -q --filter ancestor=haproxy:latest)
docker network rm $(docker network ls -q -f name=requestor_network)
```
