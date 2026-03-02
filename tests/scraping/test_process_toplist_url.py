from unittest.mock import Mock, patch
from collections import deque
from csfdtop.scraping import process_toplist_url, BasicFilmInfo


@patch("csfdtop.scraping.get_page_content")
@patch("csfdtop.scraping.get_film_list")
@patch("csfdtop.scraping.get_film_basic_info")
def test_process_toplist_url_under_limit(
    mock_get_basic_info, mock_get_film_list, mock_get_page_content
):
    # Setup
    mock_session = Mock()
    mock_soup = Mock()
    mock_get_page_content.return_value = mock_soup

    # Simulate finding 2 films
    mock_film1 = Mock()
    mock_film2 = Mock()
    mock_get_film_list.return_value = [mock_film1, mock_film2]

    # Mock conversion to BasicFilmInfo
    info1 = BasicFilmInfo("Film 1", 2000, "link1")
    info2 = BasicFilmInfo("Film 2", 2001, "link2")
    mock_get_basic_info.side_effect = [info1, info2]

    initial_deque = deque()
    initial_count = 0
    total_count = 10

    count, films_deque, soup = process_toplist_url(
        mock_session, "http://url", initial_deque, initial_count, total_count
    )

    assert count == 2
    assert len(films_deque) == 2
    assert films_deque[0] == info1
    assert films_deque[1] == info2
    assert soup == mock_soup

    mock_get_page_content.assert_called_once_with(mock_session, "http://url")
    mock_get_film_list.assert_called_once_with(mock_soup)
    assert mock_get_basic_info.call_count == 2


@patch("csfdtop.scraping.get_page_content")
@patch("csfdtop.scraping.get_film_list")
@patch("csfdtop.scraping.get_film_basic_info")
def test_process_toplist_url_reach_limit(
    mock_get_basic_info, mock_get_film_list, mock_get_page_content
):
    # Setup
    mock_session = Mock()
    mock_soup = Mock()
    mock_get_page_content.return_value = mock_soup

    # Simulate finding 5 films
    mock_films = [Mock() for _ in range(5)]
    mock_get_film_list.return_value = mock_films

    # Mock conversion
    infos = [BasicFilmInfo(f"Film {i}", 2000 + i, f"link{i}") for i in range(5)]
    mock_get_basic_info.side_effect = infos

    initial_deque = deque([BasicFilmInfo("Pre existing", 1999, "link0")])
    initial_count = 1
    total_count = 4

    count, films_deque, soup = process_toplist_url(
        mock_session, "http://url", initial_deque, initial_count, total_count
    )

    assert count == 4
    # Initial 1 + 3 new ones = 4
    assert len(films_deque) == 4

    assert films_deque[1] == infos[0]
    assert films_deque[2] == infos[1]
    assert films_deque[3] == infos[2]
    # Shouldn't contain the 4th found film (index 3 in infos)

    # Should call get_film_basic_info exactly 3 times
    assert mock_get_basic_info.call_count == 3
