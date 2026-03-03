import pytest
from csfdtop.scraping import save_results, BasicFilmInfo
from csfdtop.models import Film, Actor


@pytest.mark.django_db
def test_save_results_empty():
    save_results([])
    assert Film.objects.count() == 0
    assert Actor.objects.count() == 0


@pytest.mark.django_db
def test_save_results_new_data():
    film_info = BasicFilmInfo("Matrix", 1999, "/matrix")
    actors = ["Keanu Reeves", "Laurence Fishburne"]
    results = [(film_info, actors)]

    save_results(results)

    assert Film.objects.count() == 1
    assert Actor.objects.count() == 2

    film = Film.objects.first()
    assert film.name == "Matrix"
    assert film.year == 1999

    db_actors = film.actors.all()
    assert db_actors.count() == 2
    actor_names = set(db_actors.values_list("name", flat=True))
    assert "Keanu Reeves" in actor_names
    assert "Laurence Fishburne" in actor_names


@pytest.mark.django_db
def test_save_results_existing_actors():
    # Pre-create an actor
    Actor.objects.create(name="Keanu Reeves")

    film_info = BasicFilmInfo("Matrix", 1999, "/matrix")
    actors = ["Keanu Reeves", "Carrie-Anne Moss"]
    results = [(film_info, actors)]

    save_results(results)

    assert Film.objects.count() == 1
    assert Actor.objects.count() == 2  # 1 existing + 1 new

    film = Film.objects.get(name="Matrix")
    assert film.actors.count() == 2


@pytest.mark.django_db
def test_save_results_none_results_filtered():
    # Should handle None in results list (simulating failed scraping for some films)
    film_info = BasicFilmInfo("Valid Film", 2020, "/valid")
    results = [None, (film_info, ["Actor A"])]

    save_results(results)

    assert Film.objects.count() == 1
    assert Actor.objects.count() == 1
    assert Film.objects.first().name == "Valid Film"
