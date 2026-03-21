import pytest
from bs4 import BeautifulSoup
from csfdtop.scraping.parsing import get_pagination


BASE_URL = "/zebricky/filmy/nejlepsi/"


def test_get_pagination_success():
    html = """
    <div>
        <a href="/zebricky/filmy/nejlepsi/?from=100">100</a>
        <a href="/zebricky/filmy/nejlepsi/?from=200">200</a>
        <a href="/zebricky/filmy/nejlepsi/?from=100">100</a> <!-- Duplicate -->
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    result = get_pagination(soup, BASE_URL)

    assert len(result) == 2
    assert result[0] == (100, "/zebricky/filmy/nejlepsi/?from=100")
    assert result[1] == (200, "/zebricky/filmy/nejlepsi/?from=200")


def test_get_pagination_empty():
    html = "<div>No pagination here</div>"
    soup = BeautifulSoup(html, "html.parser")
    result = get_pagination(soup, BASE_URL)
    assert result == []


def test_get_pagination_invalid_text():
    html = """
    <div>
        <a href="/zebricky/filmy/nejlepsi/?from=100">Next</a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    with pytest.raises(ValueError):
        get_pagination(soup, BASE_URL)
