# tests/test_save_page_to_db_extra.py
import models
from models import ScrapedPage


class DummyCursor:
    def __init__(self):
        self.executed_sql = None
        self.executed_params = None
        self.closed = False

    def execute(self, sql, params=None):
        self.executed_sql = sql
        self.executed_params = params

    def close(self):
        self.closed = True


class DummyConn:
    def __init__(self, cursor_obj):
        self.cursor_obj = cursor_obj
        self.committed = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def test_save_page_to_db_with_content_and_bytes_hash(monkeypatch):
    """contentあり + hashがbytes型の場合の分岐をカバー"""
    cursor = DummyCursor()
    conn = DummyConn(cursor)
    monkeypatch.setattr(models.mysql.connector, "connect", lambda **kwargs: conn)

    # hashをbytes型にして型変換分岐を通す
    page = ScrapedPage(
        url="http://example.com",
        referrer=None,
        title="Test",
        content="Hello World",
        status_code=200,
        hash_value=b"\x12\x34\x56",  # bytes型
        error_message=None,
        processed=True,
        method="GET",
        payload=None,
    )

    models.save_page_to_db(page)

    # SQLとパラメータが渡っていること
    assert "INSERT INTO scraped_pages" in cursor.executed_sql  # type: ignore
    # hashがhex文字列に変換されていること
    assert cursor.executed_params["hash"] == "123456"  # type: ignore
    # contentのバイト数が計算されているので0ではない
    assert len(cursor.executed_params["content"].encode("utf-8")) > 0  # type: ignore
    assert conn.committed is True


def test_save_page_to_db_without_content_and_str_hash(monkeypatch):
    """contentなし + hashがstr型の場合の分岐をカバー"""
    cursor = DummyCursor()
    conn = DummyConn(cursor)
    monkeypatch.setattr(models.mysql.connector, "connect", lambda **kwargs: conn)

    # contentをNoneにしてbyte_size=0の分岐を通す
    page = ScrapedPage(
        url="http://example.com/empty",
        referrer=None,
        title="Empty",
        content=None,
        status_code=404,
        hash_value="abcdef",  # str型
        error_message="Not Found",
        processed=False,
        method="GET",
        payload=None,
    )

    models.save_page_to_db(page)

    # contentがNoneなのでbyte_size=0
    assert cursor.executed_params["content"] is None  # type: ignore
    # hashはそのまま
    assert cursor.executed_params["hash"] == "abcdef"  # type: ignore
    assert conn.committed is True
