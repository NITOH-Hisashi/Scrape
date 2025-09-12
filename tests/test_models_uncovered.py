import models
import json
from typing import Optional


class DummyCursor:
    def __init__(self, fetch_result=None, fetch_all_result=None):
        self.fetch_result = fetch_result
        self.fetch_all_result = fetch_all_result or []
        self.executed = []
        self.closed = False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self.fetch_result

    def fetchall(self):
        return self.fetch_all_result

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


def patch_conn(monkeypatch, cursor):
    conn = DummyConn(cursor)
    monkeypatch.setattr(models.mysql.connector, "connect", lambda **kwargs: conn)
    return conn


def test_get_page_by_url(monkeypatch):
    row = {"url": "http://example.com", "payload": json.dumps({"key": "value"})}
    cursor = DummyCursor(fetch_result=row)
    patch_conn(monkeypatch, cursor)
    result = models.get_page_by_url("http://example.com")
    assert result is not None and result.get("payload") == {"key": "value"}


def test_delete_page_by_url(monkeypatch):
    cursor = DummyCursor()
    conn = patch_conn(monkeypatch, cursor)
    models.delete_page_by_url("http://example.com")
    assert conn.committed


def test_update_page_content(monkeypatch):
    cursor = DummyCursor()
    conn = patch_conn(monkeypatch, cursor)
    models.update_page_content("http://example.com", "new content", b"\x12\x34")
    assert conn.committed


def test_clear_all_pages(monkeypatch):
    cursor = DummyCursor()
    conn = patch_conn(monkeypatch, cursor)
    models.clear_all_pages()
    assert conn.committed


def test_count_pages(monkeypatch):
    cursor = DummyCursor(fetch_result={"0": 42})
    patch_conn(monkeypatch, cursor)
    assert models.count_pages() == 42


def test_get_all_urls(monkeypatch):
    cursor = DummyCursor(fetch_all_result=[{"url": "http://example.com"}])
    patch_conn(monkeypatch, cursor)
    urls = list(models.get_all_urls())
    assert urls == ["http://example.com"]


def test_get_processed_urls(monkeypatch):
    cursor = DummyCursor(fetch_all_result=[{"url": "http://example.com"}])
    patch_conn(monkeypatch, cursor)
    urls = list(models.get_processed_urls())
    assert urls == ["http://example.com"]


def test_get_unprocessed_urls(monkeypatch):
    cursor = DummyCursor(fetch_all_result=[{"url": "http://example.com"}])
    patch_conn(monkeypatch, cursor)
    urls = list(models.get_unprocessed_urls())
    assert urls == ["http://example.com"]


def test_mark_all_as_processed(monkeypatch):
    cursor = DummyCursor()
    conn = patch_conn(monkeypatch, cursor)
    models.mark_all_as_processed()
    assert conn.committed


def test_mark_all_as_unprocessed(monkeypatch):
    cursor = DummyCursor()
    conn = patch_conn(monkeypatch, cursor)
    models.mark_all_as_unprocessed()
    assert conn.committed


def test_update_error_message(monkeypatch):
    cursor = DummyCursor()
    conn = patch_conn(monkeypatch, cursor)
    models.update_error_message("http://example.com", "error")
    assert conn.committed


def test_get_error_messages(monkeypatch):
    cursor = DummyCursor(
        fetch_all_result=[{"url": "http://example.com", "error_message": "error"}]
    )
    patch_conn(monkeypatch, cursor)
    result: list = list(models.get_error_messages())
    assert (
        result is not None
        and isinstance(result, list)
        and result[0]["url"] == "http://example.com"
    )


def test_clear_error_messages(monkeypatch):
    cursor = DummyCursor()
    conn = patch_conn(monkeypatch, cursor)
    models.clear_error_messages()
    assert conn.committed


def test_get_page_statistics(monkeypatch):
    stats: dict[str, int] = {
        "total_pages": 1,
        "processed_pages": 1,
        "unprocessed_pages": 0,
        "avg_content_size": 10,
    }
    cursor = DummyCursor(fetch_result=stats)
    patch_conn(monkeypatch, cursor)
    raw_stats = models.get_page_statistics()
    # Convert values to int only if they are not None and are of a compatible type
    if raw_stats and isinstance(raw_stats, dict):
        stats: dict[str, int] = {
            k: int(str(v)) if v is not None else 0 for k, v in raw_stats.items()
        }
    else:
        stats = {
            "total_pages": 0,
            "processed_pages": 0,
            "unprocessed_pages": 0,
            "avg_content_size": 0,
        }
    assert stats is not None and stats["total_pages"] == 1


def test_get_page_by_id(monkeypatch):
    row = {"url": "http://example.com"}
    cursor = DummyCursor(fetch_result=row)
    patch_conn(monkeypatch, cursor)
    result: Optional[dict] = models.get_page_by_id(1)  # type: ignore
    assert result is not None and result["url"] == "http://example.com"


def test_get_page_count(monkeypatch):
    cursor = DummyCursor(fetch_result={"COUNT(*)": 123})
    patch_conn(monkeypatch, cursor)
    assert models.get_page_count() == 123


def test_get_unprocessed_page(monkeypatch):
    row = {
        "url": "http://example.com",
        "referrer": None,
        "method": "POST",
        "payload": json.dumps({"a": 1}),
    }
    cursor = DummyCursor(fetch_result=row)
    patch_conn(monkeypatch, cursor)
    result = models.get_unprocessed_page()
    assert result is not None and result.get("url") == "http://example.com"


def test_mark_page_as_processed(monkeypatch):
    cursor = DummyCursor()
    conn = patch_conn(monkeypatch, cursor)
    models.mark_page_as_processed("http://example.com", "err")
    assert conn.committed
