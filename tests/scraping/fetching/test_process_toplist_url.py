from unittest.mock import Mock, patch
from csfdtop.scraping.parsing import BasicFilmInfo
from csfdtop.scraping.fetching import process_toplist_url


@patch("csfdtop.scraping.fetching.get_page_content")
@patch("csfdtop.scraping.fetching.get_film_list")
@patch("csfdtop.scraping.fetching.get_film_basic_info")
def test_process_toplist_url_under_limit(mock_get_basic_info, mock_get_film_list, mock_get_page_content):
    # Setup
    mock_session = Mock()
    mock_soup = Mock()
    mock_get_page_content.return_value = mock_soup

    # Simulate finding 2 films
    mock_film1 = Mock()
    mock_film2 = Mock()
    mock_get_film_list.return_value = [mock_film1, mock_film2]

    # Mock conversion to BasicFilmInfo
    info1 = BasicFilmInfo(1, "Film 1", 2000, "/film/1-film-1")
    info2 = BasicFilmInfo(1, "Film 2", 2001, "/film/2-film-2")
    mock_get_basic_info.side_effect = [info1, info2]

    initial_count = 0
    total_count = 10

    count, films_deque, soup = process_toplist_url(mock_session, "http://url", initial_count, total_count)

    assert count == 2
    assert len(films_deque) == 2
    assert films_deque[0] == info1
    assert films_deque[1] == info2
    assert soup == mock_soup

    mock_get_page_content.assert_called_once_with(mock_session, "http://url")
    mock_get_film_list.assert_called_once_with(mock_soup)
    assert mock_get_basic_info.call_count == 2


@patch("csfdtop.scraping.fetching.get_page_content")
@patch("csfdtop.scraping.fetching.get_film_list")
@patch("csfdtop.scraping.fetching.get_film_basic_info")
def test_process_toplist_url_reach_limit(mock_get_basic_info, mock_get_film_list, mock_get_page_content):
    # Setup
    mock_session = Mock()
    mock_soup = Mock()
    mock_get_page_content.return_value = mock_soup

    # Simulate finding 5 films
    mock_films = [Mock() for _ in range(5)]
    mock_get_film_list.return_value = mock_films

    # Mock conversion
    infos = [BasicFilmInfo(i, f"Film {i}", 2000 + i, f"/film/{i}-film-{i}") for i in range(5)]
    mock_get_basic_info.side_effect = infos

    initial_count = 1
    total_count = 4

    count, films_deque, soup = process_toplist_url(mock_session, "http://url", initial_count, total_count)

    assert count == 4
    # Initial 1 + 3 new ones = 4
    assert len(films_deque) == 3

    assert films_deque[0] == infos[0]
    assert films_deque[1] == infos[1]
    assert films_deque[2] == infos[2]
    # Shouldn't contain the 4th found film (index 3 in infos)

    # Should call get_film_basic_info exactly 3 times
    assert mock_get_basic_info.call_count == 3
