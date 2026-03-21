import pytest
from csfdtop.scraping.parsing import BasicFilmInfo, ActorInfo
from csfdtop.scraping.persistence import save_results
from csfdtop.models import Film, Actor


@pytest.mark.django_db
def test_save_results_empty():
    save_results([])
    assert Film.objects.count() == 0
    assert Actor.objects.count() == 0


@pytest.mark.django_db
def test_save_results_new_data():
    film_info = BasicFilmInfo(1, "Matrix", 1999, "/film/1-matrix")
    actors = [ActorInfo(csfd_id=1, name="Keanu Reeves"), ActorInfo(csfd_id=3, name="Laurence Fishburne")]
    results = [(film_info, actors)]

    save_results(results)

    assert Film.objects.count() == 1
    assert Actor.objects.count() == 2

    film = Film.objects.first()
    assert film.csfd_id == 1
    assert film.name == "Matrix"
    assert film.year == 1999

    db_actors = film.actors.all()
    assert db_actors.count() == 2
    actor_names = set(db_actors.values_list("csfd_id", "name"))
    assert (1, "Keanu Reeves") in actor_names
    assert (3, "Laurence Fishburne") in actor_names


@pytest.mark.django_db
def test_save_results_existing_actors():
    # Pre-create an actor
    Actor.objects.create(csfd_id=1, name="Keanu Reeves")

    film_info = BasicFilmInfo(1, "Matrix", 1999, "/film/1-matrix")
    actors = [ActorInfo(csfd_id=1, name="Keanu Reeves"), ActorInfo(csfd_id=2, name="Carrie-Anne Moss")]
    results = [(film_info, actors)]

    save_results(results)

    assert Film.objects.count() == 1
    assert Actor.objects.count() == 2  # 1 existing + 1 new

    film = Film.objects.get(id=film_info.csfd_id)
    assert film.actors.count() == 2


@pytest.mark.django_db
def test_save_results_none_results_filtered():
    # Should handle None in the results list (simulating failed scraping for some films)
    film_info = BasicFilmInfo(1000, "Valid Film", 2020, "/film/1000-valid")
    results = [None, (film_info, [ActorInfo(csfd_id=1, name="Actor A")])]

    save_results(results)

    assert Film.objects.count() == 1
    assert Actor.objects.count() == 1
    assert Film.objects.first().name == "Valid Film"
