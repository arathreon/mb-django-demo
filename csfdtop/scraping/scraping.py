import asyncio
import logging
import time

from django.conf import settings
from playwright.sync_api import (
    sync_playwright,
)


from csfdtop.models import Film
from csfdtop.scraping.fetching import get_basic_film_infos, get_actors, USER_AGENT
from csfdtop.scraping.persistence import save_results

logger = logging.getLogger(__name__)


def run_scraping():
    logger.info("Starting scraping")
    start_time = time.time()

    try:
        # We process only up to 10 pages, serial processing is OK
        with sync_playwright() as spw:
            browser = spw.chromium.launch(headless=True)
            try:
                context = browser.new_context(user_agent=USER_AGENT)
                basic_film_info = get_basic_film_infos(
                    context,
                    settings.TOTAL_FILM_COUNT,
                    settings.DOMAIN_URL,
                    settings.TOPLIST_URL_PART,
                )
            finally:
                browser.close()

        init_scrape_end = time.time()
        logger.info("Scraping for toplist finished in %.2f seconds", init_scrape_end - start_time)

        # This is strange behaviour and should be flagged, but if we set to find films to zero, this is correct.
        if not basic_film_info:
            logger.warning("No films found. Did you set the TOTAL_FILM_COUNT correctly?")
            return

        # Check for films that are already in the DB, we don't need to re-scrape them (assuming they don't change).
        lookup_csfd_id = [film.csfd_id for film in basic_film_info]

        existing_films = set(Film.objects.filter(csfd_id__in=lookup_csfd_id).values_list("csfd_id", flat=True))

        filtered_basic_film_info = [film for film in basic_film_info if film.csfd_id not in existing_films]

        # We may need to check hundreds of film pages for actors, we need to do it concurrently to speed up the process
        results = asyncio.run(get_actors(settings.DOMAIN_URL, filtered_basic_film_info))
        details_scrape_end = time.time()
        logger.info("Getting actors finished in %.2f seconds", details_scrape_end - init_scrape_end)

        save_results(results)
        scraping_end = time.time()
        logger.info("Saving new films to the DB in %.2f seconds", scraping_end - details_scrape_end)
        logger.info("Scraping took %.2f seconds", scraping_end - start_time)

    except Exception:
        fail_time = time.time()
        logger.exception("Scraping failed after %.2f", fail_time - start_time)
        raise
