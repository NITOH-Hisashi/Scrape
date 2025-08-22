# requests.post をモックするために必要
from unittest.mock import patch, MagicMock, Mock
from scraper import (
    get_hash,
    scrape_page,
    should_scrape,
    extract_and_save_links,
    process_single_page,
    fetch_post_content,
    scrape,
)
from models import ScrapedPage
from models import DB_CONFIG
import requests


class DummyResponse:
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.RequestException("Error")


def dummy_get(url, headers=None, timeout=None):
    return DummyResponse("<html><head><title>Test Page</title></head><body>Content</body></html>", 200)


def dummy_exception(*args, **kwargs):
    raise Exception("Test exception")


def test_db_config_override():
    DB_CONFIG.update(
        {
            "host": "localhost",
            "user": "test_user",
            "password": "test_pass",
            "database": "test_db",
        }
    )


def test_get_hash():
    text = "hello"
    expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert get_hash(text) == expected_hash


def test_scrape_page_valid_url():
    url = "https://example.com"
    page = scrape_page(url)
    assert page.url == url
    assert page.content is not None
    assert page.error_message is None


def test_scrape_page_invalid_url():
    url = "https://invalid.url"
    page = scrape_page(url)
    assert page.url == url
    assert page.error_message is not None


@patch("scraper.requests.get")
def test_scrape_page_success_http(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = (
        "<html><head><title>Test Page</title></head><body>Content</body></html>"
    )
    mock_get.return_value = mock_response
    result = scrape_page("http://example.com")
    assert result.url == "http://example.com"
    assert result.title == "Test Page"
    assert "Content" in result.content
    assert result.status_code == 200
    assert result.error_message is None


@patch("scraper.requests.get")
def test_scrape_failure_http(mock_get):
    mock_get.side_effect = Exception("Failed to fetch")
    result = scrape_page("http://example.com")
    assert result.url == "http://example.com"
    assert result.error_message == "Failed to fetch"


@patch("scraper.requests.get")
@patch("mysql.connector.connect")
def test_scrape_success_db(mock_connect, mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = (
        "<html><body><a href='https://example.com'>Link</a></body></html>"
    )

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None

    result = scrape_page("https://example.com")
    assert result.status_code == 200
    assert result.content is not None


@patch("scraper.check_robots_rules")
@patch("scraper.mark_page_as_processed")
def test_should_scrape_blocked(mock_mark, mock_check):
    mock_check.return_value = (False, 0)
    result = should_scrape("http://example.com", "TestBot")
    assert result is False
    mock_mark.assert_called_once()


@patch("scraper.check_robots_rules")
@patch("time.sleep")
def test_should_scrape_allowed_with_delay(mock_sleep, mock_check):
    mock_check.return_value = (True, 2)
    result = should_scrape("http://example.com", "TestBot")
    assert result is True
    mock_sleep.assert_called_once_with(2)


@patch("scraper.extract_links")
@patch("scraper.save_page_to_db")
def test_extract_and_save_links(mock_save, mock_extract):
    mock_extract.return_value = [("http://example.com/link", "Link Title")]
    page = MagicMock()
    page.content = "<html><a href='http://example.com/link'>Link</a></html>"
    page.url = "http://example.com"
    extract_and_save_links(page)
    mock_save.assert_called_once()


@patch("scraper.should_scrape", return_value=True)
@patch("scraper.scrape_page")
@patch("scraper.save_page_to_db")
@patch("scraper.extract_and_save_links")
@patch("scraper.mark_page_as_processed")
def test_process_single_page_success(
    mock_mark, mock_extract, mock_save, mock_scrape, mock_should
):
    mock_scrape.return_value = MagicMock(
        error_message=None, content="<html></html>", url="http://example.com"
    )
    row = {"url": "http://example.com", "referrer": None}
    process_single_page(row, "TestBot")
    mock_save.assert_called_once()
    mock_extract.assert_called_once()
    mock_mark.assert_called_once()


def test_fetch_post_content_success():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><title>Test Page</title><body>Hello</body></html>"

    with patch("scraper.requests.post", return_value=mock_response):
        page = fetch_post_content(
            "http://example.com", data={"key": "value"}, referrer="http://referrer.com"
        )
        assert isinstance(page, ScrapedPage)
        assert page.title == "Test Page"
        assert page.status_code == 200
        assert page.error_message is None


def test_process_single_page_post():
    mock_page = ScrapedPage(
        url="http://example.com",
        referrer="http://referrer.com",
        title="Mock Title",
        content="<html></html>",
        status_code=200,
        hash_value="abc123",
        method="POST",
        payload={"key": "value"},
    )

    row = {
        "url": "http://example.com",
        "referrer": "http://referrer.com",
        "method": "POST",
        "payload": {"key": "value"},
    }

    with patch("scraper.fetch_post_content", return_value=mock_page), patch(
        "scraper.check_robots_rules", return_value=(True, 0)
    ), patch("models.mysql.connector.connect", return_value=MagicMock()), patch(
        "scraper.extract_and_save_links"
    ), patch(
        "scraper.mark_page_as_processed"
    ):
        process_single_page(row, user_agent="TestBot")


def test_scrape(monkeypatch):
    # Monkey patch requests.get with our dummy_get
    monkeypatch.setattr(requests, "get", dummy_get)
    page = scrape("http://example.com")
    assert isinstance(page, ScrapedPage)
    assert page.title == "Test Page"
    assert page.status_code == 200
    assert "Content" in page.content


def test_scrape_error(monkeypatch):
    # Monkey patch requests.get to simulate an exception
    monkeypatch.setattr(__import__('requests'), "get", dummy_exception)
    page = scrape("http://example.com")
    # Check that an error message is set
    assert page.error_message == "Test exception"


def test_get_hash():
    text = "Hello"
    hash_val = get_hash(text)
    import hashlib

    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert hash_val == expected
