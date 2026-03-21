from unittest.mock import Mock, patch
from collections import deque
from csfdtop.scraping.parsing import BasicFilmInfo
from csfdtop.scraping.fetching import get_basic_film_infos


@patch("csfdtop.scraping.fetching.process_toplist_url")
@patch("csfdtop.scraping.fetching.get_pagination")
def test_get_basic_film_infos_single_page(mock_get_pagination, mock_process_toplist_url):
    # Setup
    mock_session = Mock()
    total_count = 10
    domain = "http://test.com"
    part = "/top"

    # Mock process_toplist_url to return the full count immediately
    # Returns: current_film_count, basic_film_infos, soup
    found_films = deque([BasicFilmInfo(i, f"Film {i}", 2000 + i, f"/film/{i}-film-{i}") for i in range(10)])
    mock_soup = Mock()
    mock_process_toplist_url.return_value = (10, found_films, mock_soup)

    result = get_basic_film_infos(mock_session, total_count, domain, part)

    assert len(result) == 10
    assert result == found_films

    mock_process_toplist_url.assert_called_once()
    mock_get_pagination.assert_not_called()


@patch("csfdtop.scraping.fetching.process_toplist_url")
@patch("csfdtop.scraping.fetching.get_pagination")
def test_get_basic_film_infos_multiple_pages(mock_get_pagination, mock_process_toplist_url):
    # Setup
    mock_session = Mock()
    total_count = 20
    domain = "http://test.com"
    part = "/top"

    # First page returns 10 films
    films_page1 = deque([BasicFilmInfo(i, f"Film {i}", 2000 + i, f"/film/{i}-film-{i}") for i in range(10)])
    soup_page1 = Mock()

    # Second page returns another 10 films
    films_page2 = deque(
        [BasicFilmInfo(i, f"Film {i}", 2000 + i, f"/film/{i}-film-{i}") for i in range(10)]
    )  # Accumulated
    soup_page2 = Mock()

    # Mock process_toplist_url side effects
    # First call: page 1
    # Second call: page 2
    mock_process_toplist_url.side_effect = [
        (10, films_page1, soup_page1),
        (20, films_page2, soup_page2),
    ]

    # Mock pagination
    mock_get_pagination.return_value = [(2, "/top?page=2"), (3, "/top?page=3")]

    result = get_basic_film_infos(mock_session, total_count, domain, part)

    assert len(result) == 20
    for i in range(10):
        assert result[i] == films_page1[i]
    for i in range(10):
        assert result[10 + i] == films_page2[i]

    assert mock_process_toplist_url.call_count == 2
    mock_get_pagination.assert_called_once_with(soup_page1)


@patch("csfdtop.scraping.fetching.process_toplist_url")
@patch("csfdtop.scraping.fetching.get_pagination")
def test_get_basic_film_infos_pagination_loop_break(mock_get_pagination, mock_process_toplist_url):
    # Test that loop breaks when total_count reached
    mock_session = Mock()
    total_count = 15
    domain = "http://test.com"
    part = "/top"

    # Page 1: 10 films found so far
    films1 = deque([Mock() for _ in range(10)])

    # Page 2: 15 films found in total (reached target of 15)
    # We create a specific object here to verify it is returned exactly
    films2 = deque([Mock() for _ in range(5)])

    mock_process_toplist_url.side_effect = [
        (10, films1, Mock()),  # First iteration
        (15, films2, Mock()),  # Second iteration (Limit reached)
        (20, deque([Mock()] * 20), Mock()),  # Should not be called
    ]

    mock_get_pagination.return_value = [
        (2, "/p2"),
        (3, "/p3"),  # Should not be visited
        (4, "/p4"),
    ]

    result = get_basic_film_infos(mock_session, total_count, domain, part)

    # 1. Assert the loop broke early (didn't go to page 3)
    assert mock_process_toplist_url.call_count == 2

    # 2. Assert the function returned the correct accumulated data from the last step
    assert len(result) == 15
    for i in range(10):
        assert result[i] == films1[i]
    for i in range(5):
        assert result[10 + i] == films2[i]
