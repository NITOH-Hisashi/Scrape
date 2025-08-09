import unittest
from unittest.mock import patch, MagicMock, Mock
from scraper import get_hash, scrape, should_scrape, extract_and_save_links, process_single_page

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

    @patch("scraper.requests.get")
    def test_scrape_success_http(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><head><title>Test Page</title></head><body>Content</body></html>"
        mock_get.return_value = mock_response
        result = scrape("http://example.com")
        self.assertEqual(result.url, "http://example.com")
        self.assertEqual(result.title, "Test Page")
        self.assertIn("Content", result.content)
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.error_message)

    @patch("scraper.requests.get")
    def test_scrape_failure_http(self, mock_get):
        mock_get.side_effect = Exception("Failed to fetch")
        result = scrape("http://example.com")
        self.assertEqual(result.url, "http://example.com")
        self.assertEqual(result.error_message, "Failed to fetch")

    @patch("scraper.requests.get")
    @patch("mysql.connector.connect")
    def test_scrape_success_db(self, mock_connect, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html><body><a href='https://example.com'>Link</a></body></html>"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_cursor.execute.return_value = None
        mock_conn.commit.return_value = None
        scrape("https://example.com")
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch("scraper.check_robots_rules")
    @patch("scraper.mark_page_as_processed")
    def test_should_scrape_blocked(self, mock_mark, mock_check):
        mock_check.return_value = (False, 0)
        result = should_scrape("http://example.com", "TestBot")
        self.assertFalse(result)
        mock_mark.assert_called_once()

    @patch("scraper.check_robots_rules")
    @patch("time.sleep")
    def test_should_scrape_allowed_with_delay(self, mock_sleep, mock_check):
        mock_check.return_value = (True, 2)
        result = should_scrape("http://example.com", "TestBot")
        self.assertTrue(result)
        mock_sleep.assert_called_once_with(2)

    @patch("scraper.extract_links")
    @patch("scraper.save_page_to_db")
    def test_extract_and_save_links(self, mock_save, mock_extract):
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
    def test_process_single_page_success(self, mock_mark, mock_extract, mock_save, mock_scrape, mock_should):
        mock_scrape.return_value = MagicMock(error_message=None, content="<html></html>", url="http://example.com")
        row = {"url": "http://example.com", "referrer": None}
        process_single_page(row, "TestBot")
        mock_save.assert_called_once()
        mock_extract.assert_called_once()
        mock_mark.assert_called_once()

if __name__ == "__main__":
    unittest.main()
