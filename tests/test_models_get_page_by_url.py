# tests/test_models_get_page_by_url.py
import models


class DummyCursor:
    def __init__(self, result):
        self.result = result
        self.closed = False

    def execute(self, sql, params=None):
        self.sql = sql
        self.params = params

    def fetchone(self):
        return self.result

    def close(self):
        self.closed = True


class DummyConn:
    def __init__(self, cursor_obj):
        self.cursor_obj = cursor_obj
        self.committed = False

    def cursor(self, dictionary=False):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        pass


def test_get_page_by_url(monkeypatch):
    dummy_row = {
        "url": "http://example.com",
        "referrer": None,
        "title": "Example",
        "content": "Hello",
        "payload": '{"key": "value"}',
    }
    cursor = DummyCursor(dummy_row)
    conn = DummyConn(cursor)
    monkeypatch.setattr(models.mysql.connector, "connect", lambda **kwargs: conn)

    result = models.get_page_by_url("http://example.com")
    assert result is not None, "Result should not be None"
    assert result["url"] == "http://example.com"
    assert result["payload"] == {"key": "value"}
