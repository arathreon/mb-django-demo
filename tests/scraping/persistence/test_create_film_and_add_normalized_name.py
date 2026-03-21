import pytest

from csfdtop.scraping.parsing import BasicFilmInfo
from csfdtop.scraping.persistence import create_film_and_add_normalized_name
from csfdtop.models import Film


@pytest.mark.parametrize(
    "tested_film_info, expected_result",
    [
        (
            BasicFilmInfo(csfd_id=1, name="Dobrý voják Švejk", year=1956, link="/film/1234-dobry-vojak-svejk"),
            "dobry vojak svejk",
        ),
    ],
)
def test_create_film_and_add_normalized_name(tested_film_info, expected_result):
    film = create_film_and_add_normalized_name(tested_film_info)

    assert isinstance(film, Film)
    assert film.csfd_id == tested_film_info.csfd_id
    assert film.name == tested_film_info.name
    assert film.name_normalized == expected_result
    # Ensure it's not saved to DB yet
    assert film.pk is None
