import asyncio
import collections
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from django.conf import settings
from playwright.async_api import (
    BrowserContext as AsyncBrowserContext,
    TimeoutError as AsyncPlaywrightTimeoutError,
    Error as AsyncPlaywrightError,
    async_playwright,
)
from playwright.sync_api import (
    BrowserContext as SyncBrowserContext,
    TimeoutError as SyncPlaywrightTimeoutError,
    Error as SyncPlaywrightError,
)

from csfdtop.scraping.parsing import (
    get_film_basic_info,
    process_actor_element,
    get_pagination,
    get_film_list,
    BasicFilmInfo,
    ActorInfo,
    ScrapingError,
)

logger = logging.getLogger(__name__)


# Change default headers so the request is not blocked
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0"

REQUEST_TIMEOUT = 30_000  # milliseconds


def process_toplist_url(
    browser_context: SyncBrowserContext,
    url: str,
    current_film_count: int,
    total_film_count: int,
) -> tuple[int, collections.deque[BasicFilmInfo], BeautifulSoup]:
    """Process a single toplist page and return updated film count, list of basic film infos, and the page soup."""
    soup = get_page_content(browser_context, url)
    films = get_film_list(soup)
    if (current_film_count + len(films)) < total_film_count:
        basic_film_infos = collections.deque(get_film_basic_info(film) for film in films)
        current_film_count += len(films)
    else:
        basic_film_infos = collections.deque(
            get_film_basic_info(film) for film in films[: total_film_count - current_film_count]
        )
        current_film_count = total_film_count
    return current_film_count, basic_film_infos, soup


def get_basic_film_infos(
    browser_context: SyncBrowserContext,
    total_film_count: int,
    domain_url: str,
    toplist_url_part: str,
) -> collections.deque[BasicFilmInfo]:
    """Get name, year, and link to a film page for the first X films in the toplist."""
    logger.info("Processing the first page")
    first_page = urljoin(domain_url, toplist_url_part)

    current_film_count = 0
    current_film_count, films_list, soup = process_toplist_url(
        browser_context,
        first_page,
        current_film_count,
        total_film_count,
    )

    if current_film_count != total_film_count:
        pagination_list = get_pagination(soup, toplist_url_part)

        # Either finish early to get the total number of films or go through the whole pagination list
        # This way we don't need to handle any errors
        for index, toplist_page_url_part in pagination_list:
            logger.info("Processing page %d", index)
            current_film_count, new_films_list, _ = process_toplist_url(
                browser_context,
                urljoin(domain_url, toplist_page_url_part),
                current_film_count,
                total_film_count,
            )
            films_list.extend(new_films_list)
            if current_film_count == total_film_count:
                break

    return films_list


async def fetch_film_actors(
    browser_context: AsyncBrowserContext,
    semaphore: asyncio.Semaphore,
    domain_url: str,
    film: BasicFilmInfo,
) -> tuple[BasicFilmInfo, list[ActorInfo]] | None:
    """Get actors from the film page"""
    async with semaphore:
        page = await browser_context.new_page()
        try:
            response = await page.goto(
                urljoin(domain_url, film.link), wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT
            )
            if response is None or response.status != 200:
                status = response.status if response else "no response"
                logger.error("Error while fetching film details: %s", status)
                return None
            try:
                await page.wait_for_selector("div.creators", timeout=REQUEST_TIMEOUT)
            except AsyncPlaywrightTimeoutError:
                logger.error("Couldn't find div element with creators class.")
                return None

            soup = BeautifulSoup(await page.content(), "html.parser")
            heading_element = soup.find("h4", string="Hrají:")  # type: ignore[call-overload]
            if heading_element is None:
                logger.info("Film %s does not have any actors", film.name)
                # Films may not have actors, and that results in the section not being there (e.g. Krteček)
                return film, []
            actor_elements = heading_element.find_parent("div").find_all("a")
            actors = [
                process_actor_element(actor_element)
                for actor_element in actor_elements
                if "more" not in actor_element.get("class", [])
            ]
            logger.info("Film %s has %d actors", film.name, len(actors))
            return film, actors
        except AsyncPlaywrightTimeoutError:
            logger.exception("Timeout while fetching film actors for: '%s'", film.name)
            return None
        except AsyncPlaywrightError:
            logger.exception("Playwright error while fetching film actors for: '%s'", film.name)
            return None
        finally:
            await page.close()


async def get_actors(
    domain_url: str,
    basic_film_info: list[BasicFilmInfo],
) -> list[tuple[BasicFilmInfo, list[ActorInfo]] | None]:
    # Limit concurrent requests to 20 so we're not blocked by the website
    semaphore = asyncio.Semaphore(settings.SCRAPING_MAX_CONCURRENT_REQUESTS)

    async with async_playwright() as apw:
        browser = await apw.chromium.launch(headless=True)
        try:
            context = await browser.new_context(user_agent=USER_AGENT)
            tasks = [
                fetch_film_actors(context, semaphore, domain_url, film_to_find) for film_to_find in basic_film_info
            ]
            return list(await asyncio.gather(*tasks))
        finally:
            await browser.close()


def get_page_content(browser_context: SyncBrowserContext, url: str) -> BeautifulSoup:
    """Get the content of a page from the provided URL"""
    page = browser_context.new_page()
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)
        if response is None or response.status != 200:
            status = response.status if response else "no response"
            logger.error("Error while getting page content: %s", status)
            raise ScrapingError(f"Error while getting page content: {status}")

        page.wait_for_selector("h3.film-title-norating", timeout=REQUEST_TIMEOUT)

        return BeautifulSoup(page.content(), "html.parser")
    except SyncPlaywrightTimeoutError:
        logger.exception("Timeout while getting page content for: %s", url)
        raise
    except SyncPlaywrightError:
        logger.exception("Playwright error while getting page content for: %s", url)
        raise
    finally:
        page.close()
