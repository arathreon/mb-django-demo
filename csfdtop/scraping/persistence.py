import logging
from typing import Iterable

from django.db import transaction

from csfdtop.models import Actor, Film
from csfdtop.scraping.parsing import BasicFilmInfo, ActorInfo
from csfdtop.utils import normalize_text


logger = logging.getLogger(__name__)


def save_results(results: list[tuple[BasicFilmInfo, list[ActorInfo]] | None]):
    # Filter out films that failed to fetch actors (None instead of tuple of film info and actor infos)
    clean_results = [r for r in results if r is not None]

    if not clean_results:
        logger.info("No films found with actors")
        return

    all_actor_infos = {actor for _, actor_infos in clean_results for actor in actor_infos}
    existing_actors = get_existing_actors(all_actor_infos)
    new_actors = all_actor_infos - existing_actors

    with transaction.atomic():
        Actor.objects.bulk_create([create_actor_and_add_normalized_name(actor_info) for actor_info in new_actors])
        actor_map = Actor.objects.filter(csfd_id__in=[actor_info.csfd_id for actor_info in all_actor_infos]).in_bulk(
            field_name="csfd_id"
        )

        Film.objects.bulk_create([create_film_and_add_normalized_name(film_info) for film_info, _ in clean_results])
        film_map = Film.objects.filter(csfd_id__in=[film_info.csfd_id for film_info, _ in clean_results]).in_bulk(
            field_name="csfd_id"
        )

        M2M = Film.actors.through
        M2M.objects.bulk_create(
            [
                M2M(film_id=film_map[film_info.csfd_id].id, actor_id=actor_map[actor_info.csfd_id].id)
                for film_info, actor_infos in clean_results
                for actor_info in actor_infos
            ],
            ignore_conflicts=True,
        )

    logger.info("Saved %d films and %d new actors", len(clean_results), len(new_actors))


def create_actor_and_add_normalized_name(actor_info: ActorInfo) -> Actor:
    """
    Create an Actor object and add a normalized name.

    This is because bulk_create() does not support running save() in models.
    """
    actor = Actor(csfd_id=actor_info.csfd_id, name=actor_info.name)
    actor.name_normalized = normalize_text(actor_info.name)
    return actor


def create_film_and_add_normalized_name(basic_film_info: BasicFilmInfo) -> Film:
    """
    Create a Film object and add a normalized name.

    This is because bulk_create() does not support running save() in models.
    """
    film = Film(csfd_id=basic_film_info.csfd_id, name=basic_film_info.name, year=basic_film_info.year)
    film.name_normalized = normalize_text(basic_film_info.name)
    return film


def get_existing_actors(actor_infos: Iterable[ActorInfo]) -> set[ActorInfo]:
    """Return actors existing in the database based on the passed actors"""
    existing_actors = {
        ActorInfo(csfd_id, name)
        for csfd_id, name in Actor.objects.filter(
            csfd_id__in=(actor_info.csfd_id for actor_info in actor_infos)
        ).values_list("csfd_id", "name")
    }
    return existing_actors
