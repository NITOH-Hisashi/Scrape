# tests/test_models_extra.py
import pytest
import models


class DummyCursor:
    def __init__(self, fetch_results=None):
        self._fetch_results = fetch_results or []
        self._execute_calls = []
        self._fetch_index = 0

    def execute(self, sql, params=None):
        self._execute_calls.append((sql, params))

    def fetchone(self):
        if self._fetch_index < len(self._fetch_results):
            res = self._fetch_results[self._fetch_index]
            self._fetch_index += 1
            return res
        return None

    def close(self):
        pass


class DummyConn:
    def __init__(self, cursor_obj):
        self._cursor_obj = cursor_obj
        self.committed = False

    def cursor(self):
        return self._cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        pass


def test_get_page_counts(monkeypatch):
    # 1回目のfetchone()で未処理件数、2回目で処理済み件数を返す
    cursor = DummyCursor(fetch_results=[(5,), (10,)])
    conn = DummyConn(cursor)
    monkeypatch.setattr(models.mysql.connector, "connect", lambda **kwargs: conn)

    unprocessed, processed = models.get_page_counts()
    assert unprocessed == 5
    assert processed == 10
    assert len(cursor._execute_calls) == 2


def test_reset_all_processed(monkeypatch):
    cursor = DummyCursor()
    conn = DummyConn(cursor)
    monkeypatch.setattr(models.mysql.connector, "connect", lambda **kwargs: conn)

    models.reset_all_processed()
    # UPDATE文が実行されていること
    assert any("UPDATE scraped_pages" in call[0] for call in cursor._execute_calls)
    assert conn.committed is True


@pytest.mark.parametrize("exists", [True, False])
def test_exists_in_db(monkeypatch, exists):
    cursor = DummyCursor(fetch_results=[(1,) if exists else None])
    conn = DummyConn(cursor)
    monkeypatch.setattr(models.mysql.connector, "connect", lambda **kwargs: conn)

    result = models.exists_in_db("http://example.com")
    assert result is exists
    assert "SELECT 1 FROM scraped_pages" in cursor._execute_calls[0][0]
