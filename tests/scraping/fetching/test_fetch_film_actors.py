import asyncio
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import TimeoutError, Error

from csfdtop.scraping.parsing import BasicFilmInfo, ActorInfo
from csfdtop.scraping.fetching import fetch_film_actors


@pytest.mark.asyncio
async def test_fetch_film_actors_success():
    # Setup
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_page.goto.return_value = mock_response
    mock_page.content.return_value = """
    <html>
        <div>
            <h4>Hrají:</h4>
            <div>
                <a href="/tvurce/1-actor1">Actor 1</a>
                <a href="/tvurce/2-actor2" class="more">více</a>
                <a href="/tvurce/3-actor3">Actor 3</a>
            </div>
        </div>
    </html>
    """
    mock_context.new_page.return_value = mock_page

    semaphore = asyncio.Semaphore(10)
    domain = "http://test.com"
    film = BasicFilmInfo(1234, "Matrix", 1999, "/film/1234-matrix")

    result = await fetch_film_actors(mock_context, semaphore, domain, film)

    assert result is not None
    returned_film, actors = result
    assert returned_film == film
    assert len(actors) == 2
    assert ActorInfo(csfd_id=1, name="Actor 1") in actors
    assert ActorInfo(csfd_id=3, name="Actor 3") in actors


@pytest.mark.asyncio
async def test_fetch_film_actors_http_error():
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_page.goto.return_value = mock_response
    mock_context.new_page.return_value = mock_page

    semaphore = asyncio.Semaphore(10)
    domain = "http://test.com"
    film = BasicFilmInfo(1234, "Matrix", 1999, "/film/1234-matrix")

    result = await fetch_film_actors(mock_context, semaphore, domain, film)

    assert result is None


@pytest.mark.asyncio()
async def test_fetch_film_actors_no_actors_section():
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_page.goto.return_value = mock_response
    mock_page.content.return_value = "<html><body>No actors here</body></html>"
    mock_context.new_page.return_value = mock_page

    semaphore = asyncio.Semaphore(10)
    domain = "http://test.com"
    film = BasicFilmInfo(1234, "Matrix", 1999, "/film/1234-matrix")

    result = await fetch_film_actors(mock_context, semaphore, domain, film)

    assert result is not None
    returned_film, actors = result
    assert returned_film == film
    assert actors == []


@pytest.mark.parametrize("test_error", [TimeoutError, Error])
@pytest.mark.asyncio
async def test_fetch_film_actors_connection_error(test_error):
    mock_context = AsyncMock()
    mock_page = AsyncMock()
    mock_page.goto.side_effect = test_error("Test error")
    mock_context.new_page.return_value = mock_page

    semaphore = asyncio.Semaphore(10)
    domain = "http://test.com"
    film = BasicFilmInfo(1234, "Matrix", 1999, "/film/1234-matrix")

    result = await fetch_film_actors(mock_context, semaphore, domain, film)

    assert result is None
