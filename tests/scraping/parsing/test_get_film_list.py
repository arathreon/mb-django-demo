from bs4 import BeautifulSoup
from csfdtop.scraping.parsing import get_film_list


def test_get_film_list_found():
    html = """
    <html>
        <body>
            <h3 class="film-title-norating">Film 1</h3>
            <h3 class="other-class">Not a film</h3>
            <div class="film-title-norating">Also not a film (wrong tag)</div>
            <h3 class="film-title-norating">Film 2</h3>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    results = get_film_list(soup)
    assert len(results) == 2
    assert results[0].text == "Film 1"
    assert results[1].text == "Film 2"


def test_get_film_list_empty():
    html = "<html><body></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    results = get_film_list(soup)
    assert len(results) == 0
