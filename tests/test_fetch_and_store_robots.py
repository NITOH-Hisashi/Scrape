import unittest
from unittest.mock import patch, MagicMock
from fetch_and_store_robots import fetch_and_store_robots, scrape
import requests


class TestFetchAndStoreRobots(unittest.TestCase):

    @patch("fetch_and_store_robots.mysql.connector.connect")
    @patch("fetch_and_store_robots.RobotFileParser")
    def test_fetch_and_store_robots_success(self, mock_rfp_class, mock_connect):
        # モックRobotFileParserの設定
        mock_rfp = MagicMock()
        mock_rfp.disallow_all = ["/private"]
        mock_rfp.allow_all = ["/public"]
        mock_rfp.crawl_delay.return_value = 10
        mock_rfp_class.return_value = mock_rfp

        # モックDB接続とカーソル
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # 関数呼び出し
        fetch_and_store_robots("example.com")

        # RobotFileParserの呼び出し確認
        mock_rfp.set_url.assert_called_once_with("https://example.com/robots.txt")
        mock_rfp.read.assert_called_once()

        # SQL実行確認
        self.assertTrue(mock_cursor.execute.called)
        self.assertTrue(mock_conn.commit.called)
        self.assertTrue(mock_cursor.close.called)
        self.assertTrue(mock_conn.close.called)

    @patch("fetch_and_store_robots.mysql.connector.connect")
    @patch("fetch_and_store_robots.RobotFileParser")
    def test_fetch_and_store_robots_failure(self, mock_rfp_class, mock_connect):
        # RobotFileParser.read() が例外を投げるケース
        mock_rfp = MagicMock()
        mock_rfp.read.side_effect = Exception("robots.txt unreachable")
        mock_rfp_class.return_value = mock_rfp

        # DB接続は呼ばれない想定
        mock_connect.return_value = MagicMock()

        # 標準出力の確認（必要なら capsys を使う）
        fetch_and_store_robots("invalid-domain.com")

        # read() が例外を投げたことを確認
        mock_rfp.read.assert_called_once()
        mock_connect.assert_not_called()

    def dummy_get(self, url, headers=None):
        class DummyResponse:
            def __init__(self):
                self.content = (
                    b"<html><head><title>Test Robots</title></head><body></body></html>"
                )
                self.status_code = 200

            def raise_for_status(self):
                pass

        return DummyResponse()

    def test_scrape_valid(self):
        with patch("fetch_and_store_robots.requests.get", new=self.dummy_get):
            result = scrape("http://example.com", referrer="http://referrer.com")
            self.assertEqual(result["title"], "Test Robots")
            self.assertEqual(result["status_code"], 200)

    def dummy_get_fail(self, url, headers=None):
        raise requests.RequestException("fail test")

    def test_scrape_error(self):
        with patch(
            "fetch_and_store_robots.requests.get",
            side_effect=requests.RequestException("fail test"),
        ):
            result = scrape("http://example.com")
            self.assertEqual(result["error_message"], "fail test")


if __name__ == "__main__":
    unittest.main()
