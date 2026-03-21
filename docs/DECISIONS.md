# Decisions

This document contains decisions for the mb-django-demo project. There is also an example of a full-fledged ADR
in `docs/adr/`

## Using CSFD ID for unique identification

We use CSFD IDs to uniquely identify actors and films in our database. Actor names may change in time (e.g., brothers
Wachowski are now sisters Wachowski with different first names); film names change based on provided translations
(a film may have a English name only at first, and the Czech name may come later). The CSFD IDs for films and actors are
stable and uniquely identify each film and actor regardless of their name. The disadvantage of this solution is that we
depend on an external identifier.

## Limiting the number of async fetches

We use the maximum of 20 async calls at once to scrape pages that contain film info. This is a conservative starting
point. Most sites have at least minimal protection against bots. Considering CSFD is a small Czech site, we decided
to keep the number of concurrent calls relatively low as to not be blocked. This inevitably results in slower scraping
performance. In case we need improved performance, more thorough empirical testing of the maximum concurrent calls
before blocking is necessary.

## Use Django `contains` instead of SQLite FTS 5 for full text search

We are using Django `contains` over SQLite FTS 5 for our full text search. Django `contains` sends the `LIKE` command
to our SQLite database. Since we are searching in hundreds of records in our database and this is just a demo
application, the speed is sufficient. We would need to use FTS 5 in production where thousands or even
millions of records are present in the database.


