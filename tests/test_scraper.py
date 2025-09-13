from unittest.mock import patch, MagicMock, Mock
import environment.config as config
from scraper import (
    get_hash,
    scrape_page,
    should_scrape,
    extract_and_save_links,
    process_single_page,
    fetch_post_content,
)
from models import ScrapedPage, DB_CONFIG
import requests
from scrape import scrape
import scraper


class DummyResponse:
    def __init__(self, text, status_code):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.RequestException("Error")


def dummy_get(url, headers=None, timeout=None):
    return DummyResponse(
        "<html><head><title>Test Page</title></head><body>Content</body></html>", 200
    )


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


def test_scrape_page_success_http(monkeypatch):
    monkeypatch.setattr(config, "USE_PLAYWRIGHT_PATTERNS", [])

    class MockResp:
        status_code = 200
        text = "<html><head><title>Test Page</title></head><body>OK</body></html>"
        apparent_encoding = "utf-8"

        def raise_for_status(self):
            return None

    monkeypatch.setattr(scraper.requests, "get", lambda *a, **k: MockResp())
    result = scrape_page("https://x.com")
    assert result.url == "https://x.com"
    assert result.error_message is None
    assert result.content is not None and "OK" in result.content
    assert (
        result.content
        == "<html><head><title>Test Page</title></head><body>OK</body></html>"
    )
    assert result.status_code == 200
    assert result.title == "Test Page"


def test_scrape_failure_http(monkeypatch):
    monkeypatch.setattr(config, "USE_PLAYWRIGHT_PATTERNS", [])

    def raise_exc(*a, **k):
        raise Exception("Failed to fetch")

    monkeypatch.setattr(scraper.requests, "get", raise_exc)
    result = scrape_page("https://x.com")
    assert result.url == "https://x.com"
    assert result.status_code is None
    assert result.content == ""
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
    assert result.status_code is None  # DB保存はmockで実際には行われない
    assert result.error_message is None
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


# 追加: ディレイなしパターン
@patch("scraper.check_robots_rules", return_value=(True, 0))
def test_should_scrape_allowed_no_delay(mock_check):
    result = should_scrape("http://example.com", "TestBot")
    assert result is True
    mock_check.assert_called_once()


@patch("scraper.exists_in_db", return_value=False)
@patch("scraper.extract_links")
@patch("scraper.save_page_to_db")
def test_extract_and_save_links(mock_save, mock_extract, mock_exists):
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
        error_message=None,
        content="<html><body>dummy</body></html>",
        url="http://example.com",
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


# POSTリクエスト失敗の異常系
@patch("scraper.requests.post", side_effect=Exception("POST failed"))
def test_fetch_post_content_error(mock_post):
    page = fetch_post_content("http://example.com", data={"x": 1}, referrer=None)
    assert page.error_message == "POST failed"
    assert page.status_code is None


# DB接続を完全モックしてエラー経路をカバー
@patch("scraper.should_scrape", return_value=True)
@patch("scraper.scrape_page", return_value=MagicMock(error_message="oops"))
@patch("scraper.mark_page_as_processed")
@patch("models.mysql.connector.connect", return_value=MagicMock())
def test_process_single_page_scrape_error(
    mock_connect, mock_mark, mock_scrape, mock_should
):
    row = {"url": "http://example.com"}
    process_single_page(row, "TestBot")
    mock_mark.assert_called_once()


@patch("scraper.should_scrape", return_value=True)
@patch("scraper.scrape_page")
@patch("scraper.mark_page_as_processed")
@patch("models.mysql.connector.connect", return_value=MagicMock())
def test_process_single_page_unsupported_method(
    mock_connect, mock_mark, mock_scrape, mock_should
):
    mock_scrape.return_value = MagicMock(
        url="http://example.com",
        content="<html><body>dummy</body></html>",  # ← 文字列にする
        error_message=None,
        title="Dummy Title",
        method="PUT",
        payload=None,
        referrer=None,
        status_code=200,
        hash_value="abc123",
    )
    row = {"url": "http://example.com", "method": "PUT"}
    process_single_page(row, "TestBot")
    mock_mark.assert_called_once()


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
    monkeypatch.setattr(requests, "get", dummy_get)
    page = scrape("http://example.com")
    assert isinstance(page, ScrapedPage)
    assert page.title == "Test Page"
    assert page.status_code == 200
    assert (
        page.content
        == "<html><head><title>Test Page</title></head><body>Content</body></html>"
    )


def test_scrape_error(monkeypatch):
    monkeypatch.setattr(__import__("requests"), "get", dummy_exception)
    page = scrape("http://example.com")
    assert page.error_message == "Test exception"


def test_get_hash():
    text = "Hello"
    hash_val = get_hash(text)
    import hashlib

    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert hash_val == expected
