import pytest

from csfdtop.models import Film, Actor


@pytest.fixture
def create_film_in_db(db):
    Film.objects.create(csfd_id=1, name="Matrix", year=1999)


@pytest.fixture
def create_actor_in_db(db):
    Actor.objects.create(csfd_id=1, name="Will Smith")


@pytest.mark.django_db
def test_search_api_no_query(client):
    response = client.get("/api/search/")
    assert response.status_code == 200
    assert response.json() == {"actors": [], "films": []}


@pytest.mark.django_db
def test_search_api_short_query(client):
    response = client.get("/api/search/?q=ab")
    assert response.json() == {"actors": [], "films": []}


@pytest.mark.django_db
def test_search_api_returns_empty_with_no_matches(client, create_film_in_db, create_actor_in_db):
    response = client.get("/api/search/?q=samwell")
    data = response.json()
    assert len(data["films"]) == 0
    assert len(data["actors"]) == 0


@pytest.mark.django_db
def test_search_api_returns_matching_film(client, create_film_in_db):
    response = client.get("/api/search/?q=matrix")
    data = response.json()
    assert len(data["films"]) == 1
    assert data["films"][0]["name"] == "Matrix"


@pytest.mark.django_db
def test_search_api_returns_matching_film_after_normalization(client, create_film_in_db):
    response = client.get("/api/search/?q=maťřix")
    data = response.json()
    assert len(data["films"]) == 1
    assert data["films"][0]["name"] == "Matrix"


@pytest.mark.django_db
def test_search_api_returns_matching_actor(client, create_actor_in_db):
    response = client.get("/api/search/?q=will smith")
    data = response.json()
    assert len(data["actors"]) == 1
    assert data["actors"][0]["name"] == "Will Smith"


@pytest.mark.django_db
def test_search_api_returns_matching_actor_after_normalization(client, create_actor_in_db):
    response = client.get("/api/search/?q=wiľl šmiťh")
    data = response.json()
    assert len(data["actors"]) == 1
    assert data["actors"][0]["name"] == "Will Smith"


@pytest.mark.django_db
def test_search_api_returns_matching_actor_and_movie(client):
    Film.objects.create(csfd_id=1, name="Hledá se Nemo", year=2003)
    Actor.objects.create(csfd_id=1, name="Hynek Němec")

    response = client.get("/api/search/?q=nem")
    data = response.json()
    assert len(data["actors"]) == 1
    assert data["actors"][0]["name"] == "Hynek Němec"
    assert len(data["films"]) == 1
    assert data["films"][0]["name"] == "Hledá se Nemo"
