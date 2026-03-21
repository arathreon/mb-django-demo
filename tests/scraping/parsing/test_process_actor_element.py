import pytest
from bs4 import BeautifulSoup

from csfdtop.scraping.parsing import process_actor_element, ActorInfo, ScrapingError


def test_process_actor_element_returns_ok():
    html_content = """<a href="/tvurce/4960-ryan-gosling">Ryan Gosling</a>"""
    soup = BeautifulSoup(html_content, "html.parser")
    anchor_element = soup.find("a")

    assert process_actor_element(anchor_element) == ActorInfo(4960, "Ryan Gosling")


@pytest.mark.parametrize(
    "test_input",
    [
        '<a href="/tvurce/ryan-gosling">Ryan Gosling</a>',
        "<a>Ryan Gosling</a>",
    ],
    ids=[
        "No CSFD ID in href",
        "No href",
    ],
)
def test_process_actor_element_raises_when_no_csfd_id(test_input):
    soup = BeautifulSoup(test_input, "html.parser")
    anchor_element = soup.find("a")

    with pytest.raises(ScrapingError, match="Cannot find CSFD ID for actor:"):
        process_actor_element(anchor_element)
