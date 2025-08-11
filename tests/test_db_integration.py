import unittest
from unittest.mock import patch, MagicMock
from models import (
    ScrapedPage,
    save_page_to_db,
    get_unprocessed_page,
    mark_page_as_processed,
)


class TestDBIntegration(unittest.TestCase):

    def test_scraped_page_to_dict(self):
        page = ScrapedPage(url="https://example.com", title="Example", status_code=200)
        result = page.to_dict()
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["title"], "Example")
        self.assertEqual(result["status_code"], 200)
        self.assertFalse(result["processed"])

    @patch("models.mysql.connector.connect")
    def test_save_page_to_db(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        page = ScrapedPage(url="https://example.com", title="Example", status_code=200)
        save_page_to_db(page)

        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch("models.mysql.connector.connect")
    def test_get_unprocessed_page(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "url": "https://example.com",
            "referrer": None,
            "method": "GET",
            "payload": "{}",
            "processed": False,
        }

        result = get_unprocessed_page()
        self.assertEqual(result["url"], "https://example.com")

    @patch("models.mysql.connector.connect")
    def test_mark_page_as_processed(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mark_page_as_processed("https://example.com", "No error")

        mock_cursor.execute.assert_called_with(
            "UPDATE scraped_pages"
            " SET processed = TRUE, error_message = %s"
            " WHERE url = %s",
            ("No error", "https://example.com"),
        )
        mock_conn.commit.assert_called()


if __name__ == "__main__":
    unittest.main()
