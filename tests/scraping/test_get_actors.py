import asyncio
from unittest.mock import AsyncMock, patch
from csfdtop.scraping import get_actors, BasicFilmInfo


# Helper to run async code
def run_async(coro):
    return asyncio.run(coro)


@patch("csfdtop.scraping.aiohttp.ClientSession")
@patch("csfdtop.scraping.fetch_film_actors")
def test_get_actors_orchestration(mock_fetch, mock_session_cls):
    # Setup mock session
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session

    # Mock fetch_film_actors to return specific values
    # We use side_effect to return different values based on input, or just return a simple value
    async def side_effect(session, sem, domain, film):
        return (film, [f"Actor in {film.name}", f"Second actor in {film.name}"])

    mock_fetch.side_effect = side_effect

    domain = "http://test.com"
    films = [BasicFilmInfo("Film 1", 2000, "/f1"), BasicFilmInfo("Film 2", 2001, "/f2")]

    results = run_async(get_actors(domain, films))

    assert len(results) == 2
    # Results are unordered in asyncio.gather usually, but since the list is small and strict order,
    # gather returns results in the order of awaitables.
    assert results[0] == (films[0], ["Actor in Film 1", "Second actor in Film 1"])
    assert results[1] == (films[1], ["Actor in Film 2", "Second actor in Film 2"])

    assert mock_fetch.call_count == 2

    # Verify session was created with headers
    mock_session_cls.assert_called_once()
    _, kwargs = mock_session_cls.call_args
    assert "headers" in kwargs
