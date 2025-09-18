import os
import pytest
import sqlite3
import mysql.connector
import models


@pytest.fixture(autouse=True)
def force_mysql(monkeypatch):
    monkeypatch.setenv("DB_BACKEND", "mysql")


@pytest.fixture(scope="function", autouse=True)
def db_connection(monkeypatch):
    """
    DB接続をSQLiteインメモリ or MySQLに切り替えるfixture
    TEST_DB=sqlite ならSQLite、それ以外はMySQL
    """
    db_backend = os.getenv("TEST_DB", "mysql")

    if db_backend == "sqlite":
        # SQLiteインメモリDBを利用
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        # 必要なテーブルを作成（ScrapedPage用）
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE scraped_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                content TEXT,
                referrer TEXT,
                status_code INTEGER,
                hash TEXT,
                error_message TEXT,
                processed BOOLEAN,
                method TEXT,
                payload TEXT
            )
        """
        )
        conn.commit()

        monkeypatch.setattr(models, "get_connection", lambda: conn)

    else:
        # MySQLを利用（CIでmysqlサービスを立ち上げる想定）
        def _mysql_conn():
            return mysql.connector.connect(**models.DB_CONFIG)

        monkeypatch.setattr(models, "get_connection", _mysql_conn)

    yield
    # teardown処理（SQLiteならclose）
    if db_backend == "sqlite":
        conn.close()
    else:
        pass  # MySQLは特に何もしない


@pytest.fixture(scope="function")
def clear_db():
    """各テスト前にDBのscraped_pagesテーブルをクリア"""
    conn = models.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scraped_pages")
    conn.commit()
    cursor.close()
    if isinstance(conn, sqlite3.Connection):
        # SQLiteならclose
        conn.close()
    else:
        pass  # MySQLは特に何もしない
    yield
    # 各テスト後にDBのscraped_pagesテーブルをクリア
    conn = models.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scraped_pages")
    conn.commit()
    cursor.close()
    if isinstance(conn, sqlite3.Connection):
        # SQLiteならclose
        conn.close()
    else:
        pass  # MySQLは特に何もしない


@pytest.fixture(scope="function")
def sample_data():
    """サンプルデータをDBに挿入するfixture"""
    sample_pages = [
        models.ScrapedPage(
            url="http://example.com",
            title="Example Domain",
            content="<html>...</html>",
            referrer=None,
            status_code=200,
            hash_value="abc123",
            error_message=None,
            processed=True,
        ),
        models.ScrapedPage(
            url="http://example.com/about",
            title="About Us",
            content="<html>...</html>",
            referrer="http://example.com",
            status_code=200,
            hash_value="def456",
            error_message=None,
            processed=False,
        ),
    ]
    conn = models.get_connection()
    cursor = conn.cursor()
    for page in sample_pages:
        cursor.execute(
            """
            INSERT INTO scraped_pages (
                url,
                title,
                content,
                referrer,
                status_code,
                hash,
                error_message,
                processed
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
        """,
            (
                page.url,
                page.title,
                page.content,
                page.referrer,
                page.status_code,
                page.hash,
                page.error_message,
                page.processed,
            ),
        )
    conn.commit()
    cursor.close()
    if isinstance(conn, sqlite3.Connection):
        # SQLiteならclose
        conn.close()
    else:
        pass  # MySQLは特に何もしない
    yield
    # テスト後にDBをクリア
    conn = models.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM scraped_pages")
    conn.commit()
    cursor.close()
    if isinstance(conn, sqlite3.Connection):
        # SQLiteならclose
        conn.close()
    else:
        pass  # MySQLは特に何もしない
