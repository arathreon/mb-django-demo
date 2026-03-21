# ADR-002: Use Playwright instead of requests / aiohttp

## Status

Accepted (2026-03-20). Partially supersedes ADR-001 (HTTP stack only, BeautifulSoup selection unchanged).

## Context
We've run into a problem where the CSFD website has tightened their bot protection. They implemented Anubis,
the Web AI Firewall. Anubis uses JavaScript to issue a simple challenge to a browser to check that the device
used for displaying the page truly is a browser, not a bot.

## Decision

We will use Playwright and replace `requests` and `aiohttp` calls by it. `requests` and `aiohttp` cannot use or wait
JavaScript in their requests. We also need an actual browser to solve the challenge issued by Anubis. Playwright
is more lightweight and faster to set up than Selenium. The tradeoff here is that Playwright's primary focus
is TypeScript and some functionality may not be available in Python.

## Consequences

**Good**: Works almost out-of-box (need to run a single command `playwright install` before use).
**Good**: Modern testing framework with a wide support of its community.
**Bad**: Bigger dependency.
**Bad**: Worse resource management - Playwright launches a browser which comes with cost to processing power and memory.
**Bad**: If Python API lags behind its TypeScript counterpart, workarounds may have to be found for some use cases,
  resulting in slower development.
