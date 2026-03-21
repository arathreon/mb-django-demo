import logging
import re
from typing import NamedTuple

from bs4 import Tag, BeautifulSoup, ResultSet

logger = logging.getLogger(__name__)


FILM_ID_GROUP_NAME = "film_id"
FILM_ID_RE = re.compile(rf"/film/(?P<{FILM_ID_GROUP_NAME}>\d+).*")
ACTOR_ID_GROUP_NAME = "actor_id"
ACTOR_ID_RE = re.compile(rf"/tvurce/(?P<{ACTOR_ID_GROUP_NAME}>\d+).*")
YEAR_GROUP_NAME = "year"
YEAR_RE = re.compile(rf".*(?P<{YEAR_GROUP_NAME}>\d{{4}}).*")


class ScrapingError(Exception):
    pass


class BasicFilmInfo(NamedTuple):
    csfd_id: int
    name: str
    year: int
    link: str


class ActorInfo(NamedTuple):
    csfd_id: int
    name: str


def get_film_basic_info(
    film: Tag,
) -> BasicFilmInfo:
    """Get film name, year, and link to film page"""
    title_link = film.find("a", {"class": "film-title-name"})
    info = film.find("span", {"class": "info"})
    if title_link is None or info is None:
        logger.error("The film tag has incorrect format: %s", film)
        raise ScrapingError(f"The film tag has incorrect format: {film}")

    title = title_link.get("title")
    href = title_link.get("href")

    if not isinstance(title, str) or not isinstance(href, str):
        logger.error("Cannot resolve movie title or link: %s", film)
        raise ScrapingError(f"Cannot resolve movie title or link: {film}")

    csfd_id_match = FILM_ID_RE.fullmatch(href.strip())
    if csfd_id_match is None:
        logger.error("Cannot find CSFD ID in the film link for: '%s'", title)
        raise ScrapingError(f"Cannot find CSFD ID in the film link for: '{title}'")
    csfd_id = int(csfd_id_match.group(FILM_ID_GROUP_NAME))

    # Getting year for uniqueness (assuming there are no two films with the same name AND the same year)
    match = YEAR_RE.fullmatch(info.get_text().strip())
    if match is None:
        logger.error("Cannot resolve year for movie: '%s'", title)
        raise ScrapingError(f"Cannot resolve year for movie: {film}")
    year = int(match.group(YEAR_GROUP_NAME))

    return BasicFilmInfo(csfd_id, title, year, href)


def process_actor_element(actor_element: Tag) -> ActorInfo:
    actor_name = actor_element.get_text()
    href = actor_element.get("href")
    if not isinstance(href, str) or not (actor_csfd_id_match := ACTOR_ID_RE.search(href)):
        logger.error("Cannot find CSFD ID for actor: '%s'", actor_name)
        raise ScrapingError(f"Cannot find CSFD ID for actor: '{actor_name}'")

    return ActorInfo(int(actor_csfd_id_match.group(ACTOR_ID_GROUP_NAME)), actor_name)


def get_pagination(first_page: BeautifulSoup, toplist_base_path: str) -> list[tuple[int, str]]:
    """Get pagination links for the toplist page (assuming all the links are already on the page)."""
    base = toplist_base_path.split("?")[0]  # strip query params

    # Get sorted pagination links so we can go through them one by one
    pagination = first_page.find_all("a", {"href": re.compile(rf"{re.escape(base)}\?from=\d")})
    pagination_list = sorted(
        {(int(element.get_text()), href) for element in pagination if isinstance(href := element.get("href"), str)},
        key=lambda x: x[0],
    )  # First, create a set because there are at least two instances of each link (top and bottom)
    return pagination_list


def get_film_list(document: BeautifulSoup) -> ResultSet[Tag]:
    """Get all films from the page."""
    return document.find_all("h3", {"class": "film-title-norating"})
