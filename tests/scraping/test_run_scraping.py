from unittest.mock import patch
from csfdtop.scraping import run_scraping, BasicFilmInfo


@patch("csfdtop.scraping.get_basic_film_infos")
@patch("csfdtop.scraping.get_actors")
@patch("csfdtop.scraping.save_results")
@patch("csfdtop.scraping.Film.objects")
def test_run_scraping_flow(
    mock_film_objects, mock_save_results, mock_get_actors, mock_get_basic_film_infos
):
    film1 = BasicFilmInfo("Film 1", 2020, "/f1")
    film2 = BasicFilmInfo("Film 2", 2021, "/f2")

    # Setup
    mock_get_basic_film_infos.return_value = [
        film1,
        film2,  # This one will be "existing"
    ]

    # Mock return of film hashes from DB
    f2_hash = film2.get_name_year_hash()
    mock_film_objects.filter.return_value.values_list.return_value = [f2_hash]

    # Mock get_actors return
    expected_results = [(film1, ["Actor 1", "Actor 2"])]
    mock_get_actors.return_value = expected_results

    # Run
    run_scraping()

    # Verify get_basic_film_infos called
    mock_get_basic_film_infos.assert_called_once()

    # Verify DB check
    mock_film_objects.filter.assert_called_once()

    # Verify get_actors called with FILTERED list (only Film 1)
    args, _ = mock_get_actors.call_args
    filtered_films = args[1]
    assert len(filtered_films) == 1
    assert filtered_films[0] == film1

    # Verify save_results called
    mock_save_results.assert_called_once_with(expected_results)


@patch("csfdtop.scraping.get_basic_film_infos")
def test_run_scraping_no_films(mock_get_basic_film_infos):
    mock_get_basic_film_infos.return_value = []

    with patch("csfdtop.scraping.logger") as mock_logger:
        run_scraping()
        mock_logger.warning.assert_called_with(
            "No films found. Did you set the TOTAL_FILM_COUNT correctly?"
        )
