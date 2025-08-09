class TestRobotsHandler(unittest.TestCase):

    @patch("robots_handler.mysql.connector.connect")
    @patch("robots_handler.RobotFileParser")
    def test_fetch_and_store_robots(mock_rfp_class, mock_connect):
        mock_rfp = MagicMock()
        mock_rfp.read.return_value = None
        mock_rfp.crawl_delay.return_value = 5
        mock_rfp.disallow_all = ["/private"]
        mock_rfp.allow_all = ["/public"]
        mock_rfp_class.return_value = mock_rfp
    
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
    
        fetch_and_store_robots("example.com", "MyScraperBot")
    
        mock_rfp.read.assert_called()
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch("robots_handler.mysql.connector.connect")
    @patch("robots_handler.fetch_and_store_robots")
    def test_check_robots_rules_allow(mock_fetch, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
    
        mock_cursor.fetchone.side_effect = [
            {  # robots_rules entry
                "disallow": "/private",
                "allow": "/public",
                "crawl_delay": 3
            }
        ]
    
        result, delay = check_robots_rules("https://example.com/public/page", "MyScraperBot")
        assert result is True
        assert delay == 3
