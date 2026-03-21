from unittest.mock import patch
from csfdtop.scraping.scraping import run_scraping
from csfdtop.scraping.parsing import BasicFilmInfo, ActorInfo


@patch("csfdtop.scraping.scraping.get_basic_film_infos")
@patch("csfdtop.scraping.scraping.get_actors")
@patch("csfdtop.scraping.scraping.save_results")
@patch("csfdtop.scraping.scraping.Film.objects")
def test_run_scraping_flow(mock_film_objects, mock_save_results, mock_get_actors, mock_get_basic_film_infos):
    film1 = BasicFilmInfo(1, "Film 1", 2020, "/film/1-film-1")
    film2 = BasicFilmInfo(2, "Film 2", 2021, "/film/2-film-2")

    # Setup
    mock_get_basic_film_infos.return_value = [
        film1,
        film2,  # This one will be "existing"
    ]

    # Mock return of film CSFD IDs from DB
    mock_film_objects.filter.return_value.values_list.return_value = [film2.csfd_id]

    # Mock get_actors return
    expected_results = [(film1, [ActorInfo(csfd_id=1, name="Actor 1"), ActorInfo(csfd_id=2, name="Actor 2")])]
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


@patch("csfdtop.scraping.scraping.get_basic_film_infos")
def test_run_scraping_no_films(mock_get_basic_film_infos):
    mock_get_basic_film_infos.return_value = []

    with patch("csfdtop.scraping.scraping.logger") as mock_logger:
        run_scraping()
        mock_logger.warning.assert_called_with("No films found. Did you set the TOTAL_FILM_COUNT correctly?")
