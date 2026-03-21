# ADR-001: Use BeautifulSoup instead of Scrapy

## Status

Accepted (2026-02-28). Partially superseded by ADR-002 (HTTP stack only, BeautifulSoup selection unchanged).

## Context
The project is supposed to scrape a well-defined subset of a webpage. The project scope is deliberately small - the goal
is to demonstrate understanding of scraping mechanics, model design, and data handling, not to build a production
crawler. Minimal external dependencies are preferred. The developer needs visible control over HTTP requests, parsing,
and data flow rather than framework-managed abstraction

## Decision

We will use BeautifulSoup with `requests` and `aiohttp` for HTTP. Scrapy is a scraping framework with a well-defined
API, optimized for web scraping. However, it also brings a big dependency and abstracts parts that show
the understanding of scraping. BeautifulSoup, on the other hand, is a small dependency, and the developer has a higher
degree of control over the implementation and the program flow. This comes with the trade-off of having to implement
many things ourselves that would be ready-to-use in Scrapy.

## Consequences

**Good**: No framework learning curve, faster start of development with BeautifulSoup.
**Good**: Smaller dependency.
**Bad**: No built-in request throttling, retry logic, or error handling - we need to handle it ourselves.
**Bad**: No built-in async support - we need to use aiohttp for async requests.
