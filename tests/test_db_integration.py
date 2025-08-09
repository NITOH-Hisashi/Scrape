def test_scraped_page_to_dict():
    page = ScrapedPage(url="https://example.com", title="Example", status_code=200)
    result = page.to_dict()
    assert result["url"] == "https://example.com"
    assert result["title"] == "Example"
    assert result["status_code"] == 200
    assert result["processed"] is False

@patch("mysql.connector.connect")
def test_save_page_to_db(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    page = ScrapedPage(url="https://example.com", title="Example", status_code=200)
    save_page_to_db(page)

    mock_cursor.execute.assert_called()
    mock_conn.commit.assert_called()

@patch("mysql.connector.connect")
def test_get_unprocessed_page(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {"url": "https://example.com", "processed": False}

    result = get_unprocessed_page()
    assert result["url"] == "https://example.com"

@patch("mysql.connector.connect")
def test_mark_page_as_processed(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mark_page_as_processed("https://example.com", "No error")

    mock_cursor.execute.assert_called_with(
        "UPDATE scraped_pages SET processed = TRUE, error_message = %s WHERE url = %s",
        ("No error", "https://example.com")
    )
    mock_conn.commit.assert_called()

