import pytest
from bs4 import BeautifulSoup
from csfdtop.scraping import get_film_basic_info, BasicFilmInfo, ScrapingError


def test_get_film_basic_info_success():
    html_content = """
    <div class="film-item">
        <a class="film-title-name" href="/film/123-matrix" title="Matrix">Matrix</a>
        <span class="info">(1999)</span>
    </div>
    """
    soup = BeautifulSoup(html_content, "html.parser")
    result = get_film_basic_info(soup)

    assert result.name == "Matrix"
    assert result.year == 1999
    assert result.link == "/film/123-matrix"
    assert isinstance(result, BasicFilmInfo)


def test_get_film_basic_info_missing_elements():
    # Missing title link
    html_content = """
    <div class="film-item">
        <span class="info">(1999)</span>
    </div>
    """
    soup = BeautifulSoup(html_content, "html.parser")

    with pytest.raises(ScrapingError, match="The film tag has incorrect format:"):
        get_film_basic_info(soup)


def test_get_film_basic_info_invalid_year():
    html_content = """
    <div class="film-item">
        <a class="film-title-name" href="/film/123" title="Test">Test</a>
        <span class="info">(No Year)</span>
    </div>
    """
    soup = BeautifulSoup(html_content, "html.parser")

    with pytest.raises(ScrapingError, match="Cannot resolve year for movie"):
        get_film_basic_info(soup)
