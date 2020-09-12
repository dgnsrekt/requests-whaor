# requests-haor
**Requests** with a High Availability Onion Rotator. For the filthiest scrapers on the web, that have no time for rate-limits.

You may need this.
```
docker stop $(docker ps -q --filter ancestor=osminogin/tor-simple:latest)
docker stop $(docker ps -q --filter ancestor=haproxy:latest)
docker network rm $(docker network ls -q -f name=requestor_network)
```
