import pytest
import requests
from unittest.mock import Mock
from csfdtop.scraping import get_page_content, ScrapingError


def test_get_page_content_success():
    """Test the successful retrieval of page content (BeautifulSoup object)"""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = b"<html><body><p>Test</p></body></html>"
    mock_session.get.return_value = mock_response

    soup = get_page_content(mock_session, "http://example.com")

    assert soup.find("p").text == "Test"
    mock_session.get.assert_called_with("http://example.com", timeout=10)


def test_get_page_content_404():
    """Test raises an error correctly when code is not 200"""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 404
    mock_session.get.return_value = mock_response

    with pytest.raises(ScrapingError):
        get_page_content(mock_session, "http://example.com")


def test_get_page_content_request_exception():
    """Test raises an error correctly when there is a request exception"""
    mock_session = Mock()
    mock_session.get.side_effect = requests.exceptions.RequestException

    with pytest.raises(requests.exceptions.RequestException):
        get_page_content(mock_session, "http://example.com")
