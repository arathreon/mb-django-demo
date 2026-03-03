import asyncio
from unittest.mock import AsyncMock, Mock
from aiohttp import ClientConnectorError
from csfdtop.scraping import fetch_film_actors, BasicFilmInfo


def test_fetch_film_actors_success():
    # Setup
    mock_session = Mock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = """
    <html>
        <div>
            <h4>Hrají:</h4>
            <div>
                <a href="/actor1">Actor 1</a>
                <a href="/actor2" class="more">více</a>
                <a href="/actor3">Actor 3</a>
            </div>
        </div>
    </html>
    """

    # Configure context manager
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None
    mock_session.get.return_value = mock_context

    semaphore = asyncio.Semaphore(10)
    domain = "http://test.com"
    film = BasicFilmInfo("Matrix", 1999, "/matrix")

    result = asyncio.run(fetch_film_actors(mock_session, semaphore, domain, film))

    assert result is not None
    returned_film, actors = result
    assert returned_film == film
    assert len(actors) == 2
    assert "Actor 1" in actors
    assert "Actor 3" in actors
    assert "více" not in actors


def test_fetch_film_actors_http_error():
    mock_session = Mock()
    mock_response = AsyncMock()
    mock_response.status = 404

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None
    mock_session.get.return_value = mock_context

    semaphore = asyncio.Semaphore(10)
    domain = "http://test.com"
    film = BasicFilmInfo("Matrix", 1999, "/matrix")

    result = asyncio.run(fetch_film_actors(mock_session, semaphore, domain, film))

    assert result is None


def test_fetch_film_actors_no_actors_section():
    mock_session = Mock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = "<html><body>No actors here</body></html>"

    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_response
    mock_context.__aexit__.return_value = None
    mock_session.get.return_value = mock_context

    semaphore = asyncio.Semaphore(10)
    domain = "http://test.com"
    film = BasicFilmInfo("Matrix", 1999, "/matrix")

    result = asyncio.run(fetch_film_actors(mock_session, semaphore, domain, film))

    assert result is not None
    returned_film, actors = result
    assert returned_film == film
    assert actors == []


def test_fetch_film_actors_connection_error():
    mock_session = Mock()

    mock_context = AsyncMock()
    # usage: ClientConnectorError(connection_key, os_error)
    mock_context.__aenter__.side_effect = ClientConnectorError(
        connection_key=None, os_error=OSError("Mock error")
    )
    mock_session.get.return_value = mock_context

    semaphore = asyncio.Semaphore(10)
    domain = "http://test.com"
    film = BasicFilmInfo("Matrix", 1999, "/matrix")

    result = asyncio.run(fetch_film_actors(mock_session, semaphore, domain, film))

    assert result is None
