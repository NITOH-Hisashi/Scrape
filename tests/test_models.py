from typing import Any, Dict, Optional
import unittest
from unittest.mock import patch, MagicMock
from models import (
    ScrapedPage,
    save_page_to_db,
    get_unprocessed_page,
    mark_page_as_processed,
)


class TestScrapedPage(unittest.TestCase):
    def test_to_dict_serialization(self):
        page = ScrapedPage(
            url="https://example.com",
            referrer="https://referrer.com",
            title="Example Title",
            content="<html>...</html>",
            status_code=200,
            hash_value="abc123",
            error_message=None,
            method="POST",
            payload={"key": "value"},
        )
        result = page.to_dict()
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["method"], "POST")
        self.assertEqual(result["payload"], '{"key": "value"}')
        self.assertFalse(result["processed"])


class TestDBFunctions(unittest.TestCase):

    @patch("models.mysql.connector.connect")
    def test_save_page_to_db(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        page = ScrapedPage(url="https://example.com")
        save_page_to_db(page)

        self.assertTrue(mock_cursor.execute.called)
        self.assertTrue(mock_conn.commit.called)

    @patch("models.mysql.connector.connect")
    def test_get_unprocessed_page(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "url": "https://example.com",
            "referrer": "https://referrer.com",
            "method": "POST",
            "payload": '{"key": "value"}',
        }

        result: Optional[Dict[str, Any]] = get_unprocessed_page()
        self.assertIsNotNone(result)
        self.assertEqual(result["url"], "https://example.com")
        self.assertEqual(result["method"], "POST")
        self.assertEqual(result["payload"], {"key": "value"})

    @patch("models.mysql.connector.connect")
    def test_mark_page_as_processed(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mark_page_as_processed("https://example.com", "404 Not Found")

        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
