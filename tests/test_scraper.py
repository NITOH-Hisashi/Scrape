import unittest
from scraper import get_hash, scrape
from unittest.mock import patch, Mock

class TestScraper(unittest.TestCase):
    def test_get_hash(self):
        text = "hello"
        expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.assertEqual(get_hash(text), expected_hash)

    def test_scrape_valid_url(self):
        url = "https://example.com"
        page = scrape(url)
        self.assertEqual(page.url, url)
        self.assertIsNotNone(page.content)
        self.assertIsNone(page.error_message)

    def test_scrape_invalid_url(self):
        url = "https://invalid.url"
        page = scrape(url)
        self.assertEqual(page.url, url)
        self.assertIsNotNone(page.error_message)

@patch("mysql.connector.connect")
def test_scrape_success(mock_connect, mock_get):
    # モックDB接続の設定
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.execute.return_value = None

    # モックHTTPレスポンス
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "<html><body><a href='https://example.com'>Link</a></body></html>"

    # 実行
    scrape("https://example.com")

from unittest.mock import patch, MagicMock
from scraper import scrape

@patch("mysql.connector.connect")
@patch("requests.get")
def test_scrape_success(mock_get, mock_connect):
    # モックHTTPレスポンス
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "<html><body><a href='https://example.com'>Link</a></body></html>"

    # モックDB接続とカーソル
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # 重複チェック用
    mock_cursor.execute.return_value = None
    mock_conn.commit.return_value = None

    # 実行
    scrape("https://example.com")

    # アサーション（任意）
    mock_cursor.execute.assert_called()
    mock_conn.commit.assert_called()

@patch('scraper.requests.get')
def test_scrape_success(mock_get):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = '<html><head><title>Test Page</title></head><body>Content</body></html>'
    mock_get.return_value = mock_response

    result = scrape('http://example.com')

    assert result.url == 'http://example.com'
    assert result.title == 'Test Page'
    assert 'Content' in result.content
    assert result.status_code == 200
    assert result.error_message is None

@patch('scraper.requests.get')
def test_scrape_failure(mock_get):
    mock_get.side_effect = Exception('Failed to fetch')

    result = scrape('http://example.com')

    assert result.url == 'http://example.com'
    assert result.error_message == 'Failed to fetch'


if __name__ == '__main__':
    unittest.main()
