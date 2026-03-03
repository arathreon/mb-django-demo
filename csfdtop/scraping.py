import asyncio
import collections
import logging
import re
import time
from typing import NamedTuple
from urllib.parse import urljoin

import aiohttp
import requests
from aiohttp import ClientConnectorError
from bs4 import BeautifulSoup, ResultSet, Tag
from django.conf import settings
from django.db import transaction
from requests import Session

from csfdtop.models import Film, Actor
from csfdtop.utils import get_name_year_hash, normalize_text

logger = logging.getLogger(__name__)

# Change default headers so the request is not blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0"
}
REQUEST_TIMEOUT = 10  # seconds

YEAR_GROUP_NAME = "year"
YEAR_RE = re.compile(rf".*(?P<{YEAR_GROUP_NAME}>\d{{4}}).*")


class ScrapingError(Exception):
    pass


class BasicFilmInfo(NamedTuple):
    name: str
    year: int
    link: str

    def get_name_year_hash(self):
        return get_name_year_hash(self.name, self.year)


def get_page_content(request_session: Session, url: str) -> BeautifulSoup:
    """Get the content of a page from the provided URL"""
    try:
        page = request_session.get(url, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException:
        logger.exception("Error while getting page content")
        raise

    if page.status_code != 200:
        logger.error(f"Error while getting page content: {page.status_code}")
        raise ScrapingError(f"Error while getting page content: {page.status_code}")

    return BeautifulSoup(page.content.decode(), "html.parser")


def get_film_list(document: BeautifulSoup) -> ResultSet[Tag]:
    """Get all films from the page."""
    return document.find_all("h3", {"class": "film-title-norating"})


def get_film_basic_info(
    film: Tag,
) -> BasicFilmInfo:
    """Get film name, year, and link to film page"""
    title_link = film.find("a", {"class": "film-title-name"})
    info = film.find("span", {"class": "info"})
    if title_link is None or info is None:
        msg = f"The film tag has incorrect format: {film}"
        logger.error(msg)
        raise ScrapingError(msg)
    if "title" not in title_link.attrs or "href" not in title_link.attrs:
        msg = f"Cannot resolve movie title or link: {film}"
        logger.error(msg)
        raise ScrapingError(msg)

    # Getting year for uniqueness (assuming there are no two films with the same name AND the same year)
    match = YEAR_RE.fullmatch(info.get_text().strip())
    if match is None:
        msg = f"Cannot resolve year for movie: {film}"
        logger.error(msg)
        raise ScrapingError(msg)
    year = int(match.group(YEAR_GROUP_NAME))

    return BasicFilmInfo(title_link.get("title"), year, title_link.get("href"))


def process_toplist_url(
    request_session: Session,
    url: str,
    basic_film_infos: collections.deque[BasicFilmInfo],
    current_film_count: int,
    total_film_count: int,
) -> tuple[int, collections.deque[BasicFilmInfo], BeautifulSoup]:
    """Process a single toplist page and return updated film count, list of basic film infos, and the page soup."""
    soup = get_page_content(request_session, url)
    films = get_film_list(soup)
    if (current_film_count + len(films)) < total_film_count:
        basic_film_infos.extend([get_film_basic_info(film) for film in films])
        current_film_count += len(films)
    else:
        basic_film_infos.extend(
            [
                get_film_basic_info(film)
                for film in films[: total_film_count - current_film_count]
            ]
        )
        current_film_count = total_film_count
    return current_film_count, basic_film_infos, soup


def get_pagination(first_page: BeautifulSoup) -> list[tuple[int, str]]:
    """Get pagination links for the toplist page (assuming all the links are already on the page)."""
    # Get sorted pagination links so we can go through them one by one
    pagination = first_page.find_all(
        "a", {"href": re.compile(r"/zebricky/filmy/nejlepsi/\?from=\d")}
    )
    pagination_list = sorted(
        {(int(element.get_text()), element.get("href")) for element in pagination},
        key=lambda x: x[0],
    )  # First, create a set because there are at least two instances of each link (top and bottom)
    return pagination_list


def get_basic_film_infos(
    request_session: Session,
    total_film_count: int,
    domain_url: str,
    toplist_url_part: str,
) -> collections.deque[BasicFilmInfo]:
    """Get name, year, and link to a film page for the first X films in the toplist."""
    logger.info("Processing the first page")
    first_page = urljoin(domain_url, toplist_url_part)

    films_list = collections.deque()
    current_film_count = 0
    current_film_count, films_list, soup = process_toplist_url(
        request_session,
        first_page,
        films_list,
        current_film_count,
        total_film_count,
    )

    if current_film_count != total_film_count:
        pagination_list = get_pagination(soup)

        # Either finish early to get the total number of films or go through the whole pagination list
        # This way we don't need to handle any errors
        for index, toplist_page_url_part in pagination_list:
            logger.info(f"Processing page {index}")
            current_film_count, films_list, _ = process_toplist_url(
                request_session,
                urljoin(domain_url, toplist_page_url_part),
                films_list,
                current_film_count,
                total_film_count,
            )
            if current_film_count == total_film_count:
                break

    return films_list


async def fetch_film_actors(
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    domain_url: str,
    film: BasicFilmInfo,
):
    """Get actors from the film page"""
    async with semaphore:
        try:
            async with session.get(urljoin(domain_url, film.link)) as response:
                if response.status != 200:
                    logger.error(
                        f"Error while fetching film details: {response.status}"
                    )
                    return None
                soup = BeautifulSoup(await response.text(), "html.parser")
                heading_element = soup.find("h4", string="Hrají:")
                if heading_element is None:
                    logger.info(f"Film {film.name} does not have any actors")
                    # Films may not have actors, and that results in the section not being there (e.g. Krteček)
                    return film, []
                actor_elements = heading_element.find_parent("div").find_all("a")
                actors = [
                    actor_element.get_text()
                    for actor_element in actor_elements
                    if "more" not in actor_element.get("class", [])
                ]
                logger.info(f"Film {film.name} has {len(actors)} actors")
                return film, actors
        except ClientConnectorError:
            logger.exception("Error while fetching film actors")
            return None


async def get_actors(
    domain_url: str,
    basic_film_info: list[BasicFilmInfo],
):
    # Limit concurrent requests to 20 so we're not blocked by the website
    semaphore = asyncio.Semaphore(20)

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks = [
            fetch_film_actors(session, semaphore, domain_url, film_to_find)
            for film_to_find in basic_film_info
        ]
        return await asyncio.gather(*tasks)


def create_actor_and_add_normalized_name(actor_name: str) -> Actor:
    """
    Create an Actor object and add normalized name.

    This is because bulk_create() does not support running save() in models.
    """
    actor = Actor(name=actor_name)
    actor.name_normalized = normalize_text(actor_name)
    return actor


def save_results(results: list[tuple[BasicFilmInfo, list[str]]]):
    # Filter out films without actors because they failed to scrape
    clean_results = list(filter(lambda x: x is not None, results))

    if not clean_results:
        logger.info("No films found with actors")
        return

    all_actor_names = {
        actor for _, actor_names in clean_results for actor in actor_names
    }
    existing_actors = Actor.objects.filter(name__in=all_actor_names).values_list(
        "name", flat=True
    )
    new_actors = all_actor_names - set(existing_actors)
    Actor.objects.bulk_create(
        [create_actor_and_add_normalized_name(actor_name) for actor_name in new_actors]
    )
    actor_map = Actor.objects.filter(name__in=all_actor_names).in_bulk(
        field_name="name"
    )

    with transaction.atomic():
        for film_info, actor_names in clean_results:
            film, _ = Film.objects.get_or_create(
                name=film_info.name,
                year=film_info.year,
            )

            actors = [actor_map[name] for name in actor_names if name in actor_map]
            film.actors.set(actors)

    logger.info(f"Saved {len(clean_results)} films and {len(new_actors)} new actors")


def run_scraping():
    logger.info("Starting scraping")
    start_time = time.time()

    # We process only up to 10 pages, serial processing is OK
    with requests.Session() as request_session:
        request_session.headers.update(HEADERS)
        basic_film_info = get_basic_film_infos(
            request_session,
            settings.TOTAL_FILM_COUNT,
            settings.DOMAIN_URL,
            settings.TOPLIST_URL_PART,
        )

    init_scrape_end = time.time()
    logger.info(
        f"Scraping for toplist finished in {init_scrape_end - start_time} seconds"
    )

    # This is strange behaviour and should be flagged, but if we set to find films to zero this is correct.
    if not basic_film_info:
        logger.warning("No films found. Did you set the TOTAL_FILM_COUNT correctly?")
        return

    # Check for films that are already in the DB, we don't need to re-scrape them (assuming they don't change).
    lookup_hash = [film.get_name_year_hash() for film in basic_film_info]

    existing_films = set(
        Film.objects.filter(name_year_hash__in=lookup_hash).values_list(
            "name_year_hash", flat=True
        )
    )

    filtered_basic_film_info = [
        film
        for film in basic_film_info
        if film.get_name_year_hash() not in existing_films
    ]

    # We may need to check hundreds of film pages for actors, we need to do it concurrently to speed up the process
    results = asyncio.run(get_actors(settings.DOMAIN_URL, filtered_basic_film_info))
    details_scrape_end = time.time()
    logger.info(
        f"Getting actors finished in {details_scrape_end - init_scrape_end} seconds"
    )

    save_results(results)
    scraping_end = time.time()
    logger.info(
        f"Saving new films to the DB in {scraping_end - details_scrape_end} seconds"
    )
    logger.info(f"Scraping took {scraping_end - start_time} seconds")
