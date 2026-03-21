import pytest
from unittest.mock import Mock
from csfdtop.scraping.parsing import ScrapingError
from csfdtop.scraping.fetching import get_page_content, REQUEST_TIMEOUT
from playwright.sync_api import TimeoutError, Error


def test_get_page_content_success():
    """Test the successful retrieval of page content (BeautifulSoup object)"""
    mock_context = Mock()
    mock_response = Mock()
    mock_response.status = 200
    mock_page = Mock()
    mock_page.goto.return_value = mock_response
    mock_page.content.return_value = "<html><body><p>Test</p></body></html>"
    mock_context.new_page.return_value = mock_page

    soup = get_page_content(mock_context, "http://example.com")

    assert soup.find("p").text == "Test"
    mock_context.new_page.assert_called()
    mock_page.goto.assert_called_with("http://example.com", wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT)


def test_get_page_content_404():
    """Test raises an error correctly when code is not 200"""
    mock_context = Mock()
    mock_response = Mock()
    mock_response.status = 404
    mock_page = Mock()
    mock_page.goto.return_value = mock_response
    mock_context.new_page.return_value = mock_page

    with pytest.raises(ScrapingError):
        get_page_content(mock_context, "http://example.com")


@pytest.mark.parametrize("test_error", [TimeoutError, Error])
def test_get_page_content_request_exception(test_error):
    """Test raises an error correctly when there is a request exception"""
    mock_context = Mock()
    mock_page = Mock()
    mock_page.goto.side_effect = test_error("Test error")
    mock_context.new_page.return_value = mock_page

    with pytest.raises(test_error):
        get_page_content(mock_context, "http://example.com")
