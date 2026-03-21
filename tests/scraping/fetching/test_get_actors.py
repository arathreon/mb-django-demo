from unittest.mock import AsyncMock, patch

import pytest

from csfdtop.scraping.parsing import BasicFilmInfo, ActorInfo
from csfdtop.scraping.fetching import get_actors, USER_AGENT


@patch("csfdtop.scraping.fetching.async_playwright")
@patch("csfdtop.scraping.fetching.fetch_film_actors")
@pytest.mark.asyncio
async def test_get_actors_orchestration(mock_fetch, mock_session_cls):
    # Setup mock session
    mock_playwright = AsyncMock()
    mock_browser = AsyncMock()
    mock_context = AsyncMock()
    mock_browser.new_context.return_value = mock_context
    mock_playwright.chromium.launch.return_value = mock_browser
    mock_session_cls.return_value.__aenter__.return_value = mock_playwright

    # Mock fetch_film_actors to return specific values
    # We use side_effect to return different values based on input, or just return a simple value
    async def side_effect(context, sem, domain, film):
        return film, [
            ActorInfo(csfd_id=(film.csfd_id - 1) * 2 + 1, name=f"Actor in {film.name}"),
            ActorInfo(csfd_id=(film.csfd_id - 1) * 2 + 2, name=f"Second actor in {film.name}"),
        ]

    mock_fetch.side_effect = side_effect

    domain = "http://test.com"
    films = [BasicFilmInfo(1, "Film 1", 2000, "/film/1-film-1"), BasicFilmInfo(2, "Film 2", 2001, "/film/2-film-2")]

    results = await get_actors(domain, films)

    assert len(results) == 2
    # Results are unordered in asyncio.gather usually, but since the list is small and strict order,
    # gather returns results in the order of awaitables.
    assert results[0] == (
        films[0],
        [ActorInfo(csfd_id=1, name="Actor in Film 1"), ActorInfo(csfd_id=2, name="Second actor in Film 1")],
    )
    assert results[1] == (
        films[1],
        [ActorInfo(csfd_id=3, name="Actor in Film 2"), ActorInfo(csfd_id=4, name="Second actor in Film 2")],
    )

    assert mock_fetch.call_count == 2

    # Verify session was created with headers
    mock_session_cls.assert_called_once()
    mock_playwright.chromium.launch.assert_called_once_with(headless=True)
    mock_browser.new_context.assert_called_once_with(user_agent=USER_AGENT)
