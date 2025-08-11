import unittest
from unittest.mock import patch, MagicMock
from fetch_and_store_robots import store_robots_txt


class TestFetchAndStoreRobots(unittest.TestCase):

    @patch("fetch_and_store_robots.mysql.connector.connect")
    def test_store_robots_txt_db_interaction(self, mock_connect):
        # モック接続とカーソルの設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # 関数呼び出し
        store_robots_txt()

        # DB接続が1回呼ばれたか確認
        mock_connect.assert_called_once()

        # SQL実行が呼ばれたか確認
        self.assertTrue(mock_cursor.execute.called)

        # コミットとクローズ処理の確認
        self.assertTrue(mock_conn.commit.called)
        self.assertTrue(mock_cursor.close.called)
        self.assertTrue(mock_conn.close.called)


if __name__ == "__main__":
    unittest.main()
