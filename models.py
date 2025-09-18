from datetime import datetime
import mysql.connector
import json
from typing import Optional, Dict, Any, Tuple, Union
import os
import sqlite3
import hashlib


# 環境変数からDB設定を取得
DB_BACKEND = os.getenv("DB_BACKEND", "mysql")

if DB_BACKEND == "sqlite":
    DB_CONFIG = {"database": os.getenv("SQLITE_DB", ":memory:")}
else:
    DB_CONFIG = {
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", "root"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME", "scraping_db"),
    }


class ScrapedPage:
    def __init__(
        self,
        url,
        title,
        content,
        referrer=None,
        status_code=None,
        hash_value=None,
        error_message=None,
        method="GET",
        processed=False,
        payload=None,
    ):
        self.url = url
        self.url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()
        self.referrer = referrer
        self.fetched_at = datetime.now()
        self.title = title
        self.content = content
        self.status_code = status_code
        self.hash = hash_value
        self.error_message = error_message
        self.processed = processed
        self.method = method
        self.payload = payload or {}

    def to_dict(self):
        return {
            "url": self.url,
            "referrer": self.referrer,
            "fetched_at": self.fetched_at,
            "title": self.title,
            "content": self.content,
            "status_code": self.status_code,
            "hash": self.hash,
            "error_message": self.error_message,
            "processed": self.processed,
            "method": self.method,
            "payload": json.dumps(self.payload),
            "url_hash": self.url_hash,
            "id": None,  # idはDB挿入時に自動生成されるためNoneで初期化
            "url_domain": self.get_domain(self.url),
            "referrer_domain": (
                self.get_domain(self.referrer) if self.referrer else None
            ),
        }

    @staticmethod
    def get_domain(url: Optional[str]) -> Optional[str]:
        from urllib.parse import urlparse

        if not url:
            return None
        parsed = urlparse(url)
        return parsed.netloc


def save_page_to_db(page: ScrapedPage):
    """スクレイピング結果をデータベースに保存（MySQL/SQLite両対応）"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        page_dict = page.to_dict()

        byte_size = (
            len(page_dict["content"].encode("utf-8", errors="ignore"))
            if page_dict.get("content")
            else 0
        )
        print(f"{page_dict['url']} page_dict content size: {byte_size} bytes")

        # hash が bytes の場合は文字列化
        if page_dict.get("hash") is not None and not isinstance(page_dict["hash"], str):
            # bytesやその他の型を文字列化（例: SHA256のbytes → hex文字列）
            page_dict["hash"] = (
                page_dict["hash"].hex()
                if hasattr(page_dict["hash"], "hex")
                else str(page_dict["hash"])
            )

        if DB_BACKEND == "mysql":
            # MySQL 用: ON DUPLICATE KEY UPDATE
            cursor.execute(
                """
                INSERT INTO scraped_pages (
                    url,
                    url_hash,
                    fetched_at,
                    title,
                    content,
                    referrer,
                    status_code,
                    hash,
                    error_message,
                    processed,
                    method,
                    payload
                )
                VALUES (
                    %(url)s,
                    %(url_hash)s,
                    %(fetched_at)s,
                    %(title)s,
                    %(content)s,
                    %(referrer)s,
                    %(status_code)s,
                    %(hash)s,
                    %(error_message)s,
                    %(processed)s,
                    %(method)s,
                    %(payload)s
                )
                ON DUPLICATE KEY UPDATE
                    referrer = COALESCE(VALUES(referrer), referrer),
                    fetched_at = CURRENT_TIMESTAMP,
                    title = CASE
                        WHEN (title IS NULL OR title = '') THEN VALUES(title)
                        ELSE title
                    END,
                    content = COALESCE(VALUES(content), content),
                    status_code = COALESCE(VALUES(status_code), status_code),
                    hash = COALESCE(VALUES(hash), hash),
                    error_message = VALUES(error_message),
                    processed = VALUES(processed),
                    method = VALUES(method),
                    payload = VALUES(payload)
                """,
                page_dict,
            )
        else:
            # SQLite 用: INSERT OR REPLACE
            cursor.execute(
                """
                INSERT OR REPLACE INTO scraped_pages (
                    url,
                    url_hash,
                    fetched_at,
                    error_message,
                    processed,
                    method,
                    payload,
                    title,
                    content,
                    referrer,
                    status_code,
                    hash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    page_dict["url"],
                    page_dict["url_hash"],
                    page_dict["fetched_at"],
                    page_dict["title"],
                    page_dict["content"],
                    page_dict["referrer"],
                    page_dict["status_code"],
                    page_dict["hash"],
                    page_dict["error_message"],
                    page_dict["processed"],
                    page_dict["method"],
                    page_dict["payload"],
                ),
            )

        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_unprocessed_page() -> Optional[Dict[str, Any]]:
    """未処理のページを1件取得（POST対応）"""
    conn = get_connection()
    cursor = get_cursor(conn, dictionary=True)
    try:
        cursor.execute(
            """
            SELECT url, referrer, method, payload
            FROM scraped_pages
            WHERE processed = FALSE
            ORDER BY id ASC
            LIMIT 1
            """
        )
        row = cursor.fetchone()  # type: ignore
        if row:
            row: Optional[Dict[str, Any]] = row
            # payloadがJSON文字列なら辞書に変換
            # type: Optional[Dict[str, Any]]
            payload = (
                json.loads(row.get("payload") or "{}") if row.get("payload") else {}
            )
            return {
                "url": row["url"],
                "referrer": row["referrer"],
                "method": row.get("method", "GET").upper(),
                "payload": payload,
            }
        return {
            "url": None,
            "referrer": None,
            "method": "GET",
            "payload": {},
        }
    finally:
        cursor.close()
        conn.close()


def mark_page_as_processed(url, error_message=None):
    """ページを処理済みとしてマーク"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE scraped_pages"
            " SET processed = TRUE, error_message = %s"
            " WHERE url = %s",
            (error_message, url),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_page_counts():
    """未処理件数と処理済み件数を返す"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM scraped_pages WHERE processed = FALSE")
        unprocessed_row: Optional[Union[Tuple[Any, ...], Dict[str, Any]]] = (
            cursor.fetchone()
        )
        unprocessed_count = unprocessed_row[0] if unprocessed_row else 0  # type: ignore
        cursor.execute("SELECT COUNT(*) FROM scraped_pages WHERE processed = TRUE")
        processed_row: Optional[Union[Tuple[Any, ...], Dict[str, Any]]] = (
            cursor.fetchone()
        )
        processed_count = processed_row[0] if processed_row else 0  # type: ignore
        return unprocessed_count, processed_count
    finally:
        cursor.close()
        conn.close()


def reset_all_processed():
    """全レコードの processed を FALSE にする"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE scraped_pages SET processed = FALSE")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def exists_in_db(url: str) -> bool:
    """指定URLが scraped_pages に存在するかを返す"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM scraped_pages WHERE url = %s LIMIT 1", (url,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        conn.close()


def get_page_by_url(url: str):
    """指定URLのページ情報を取得"""
    conn = get_connection()
    cursor = get_cursor(conn, dictionary=True)
    try:
        cursor.execute("SELECT * FROM scraped_pages WHERE url = %s LIMIT 1", (url,))
        row = cursor.fetchone()  # type: ignore
        if row:
            row: Optional[Dict[str, Any]] = row
            if row.get("payload"):
                row["payload"] = json.loads(row["payload"])
            return row
        return None
    finally:
        cursor.close()
        conn.close()


def delete_page_by_url(url: str):
    """指定URLのページ情報を削除"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM scraped_pages WHERE url = %s", (url,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def update_page_content(url: str, content: str, hash_value):
    """指定URLのページ内容とハッシュを更新"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        hash_str = (
            (hash_value.hex() if hasattr(hash_value, "hex") else str(hash_value))
            if hash_value is not None
            else None
        )
        cursor.execute(
            "UPDATE scraped_pages SET content = %s, `hash` = %s WHERE url = %s",
            (content, hash_str, url),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def clear_all_pages():
    """scraped_pages テーブルの全レコードを削除"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM scraped_pages")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def count_pages():
    """scraped_pages テーブルの全レコード数を返す"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM scraped_pages")
        row = cursor.fetchone()  # type: ignore
        if row:
            row: Optional[Dict[str, Any]] = row
            return row["0"]
    finally:
        cursor.close()
        conn.close()


def get_all_urls():
    """scraped_pages テーブルの全URLをリストで返す"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT url FROM scraped_pages")
        rows = cursor.fetchall()  # type: ignore
        if rows:
            rows: list = rows
            for row in rows:
                row: Optional[Dict[str, Any]] = row
                if row:
                    yield row["url"]
    finally:
        cursor.close()
        conn.close()


def get_processed_urls():
    """処理済みのURLをリストで返す"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT url FROM scraped_pages WHERE processed = TRUE")
        rows = cursor.fetchall()  # type: ignore
        if rows:
            rows: list = rows
            for row in rows:
                row: Optional[Dict[str, Any]] = row
                if row:
                    yield row["url"]
    finally:
        cursor.close()
        conn.close()


def get_unprocessed_urls():
    """未処理のURLをリストで返す"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT url FROM scraped_pages WHERE processed = FALSE")
        rows = cursor.fetchall()  # type: ignore
        if rows:
            rows: list = rows
            for row in rows:
                row: Optional[Dict[str, Any]] = row
                if row:
                    yield row["url"]
    finally:
        cursor.close()
        conn.close()


def mark_all_as_processed():
    """全ページを処理済みとしてマーク"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE scraped_pages SET processed = TRUE")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def mark_all_as_unprocessed():
    """全ページを未処理としてマーク"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE scraped_pages SET processed = FALSE")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def update_error_message(url: str, error_message: str):
    """指定URLのエラーメッセージを更新"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE scraped_pages SET error_message = %s WHERE url = %s",
            (error_message, url),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_error_messages():
    """全ページのエラーメッセージを取得"""
    conn = get_connection()
    cursor = get_cursor(conn, dictionary=True)
    try:
        cursor.execute(
            "SELECT url,"
            "error_message"
            "FROM scraped_pages"
            "WHERE error_message IS NOT NULL"
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def clear_error_messages():
    """全ページのエラーメッセージをクリア"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE scraped_pages SET error_message = NULL")
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_page_statistics():
    """ページの統計情報を取得"""
    conn = get_connection()
    cursor = get_cursor(conn, dictionary=True)
    try:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_pages,
                SUM(
                CASE WHEN processed = TRUE
                THEN 1 ELSE 0 END
                ) AS processed_pages,
                SUM(
                CASE WHEN processed = FALSE
                THEN 1 ELSE 0 END
                ) AS unprocessed_pages,
                AVG(LENGTH(content)) AS avg_content_size
            FROM scraped_pages
        """
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_page_by_id(page_id: int):
    """指定IDのページ情報を取得"""
    conn = get_connection()
    cursor = get_cursor(conn, dictionary=True)
    try:
        cursor.execute("SELECT * FROM scraped_pages WHERE id = %s", (page_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def get_page_count():
    """scraped_pages テーブルの全レコード数を返す"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM scraped_pages")
        return cursor.fetchone()["COUNT(*)"]  # type: ignore
    finally:
        cursor.close()
        conn.close()


def get_connection():
    if DB_BACKEND == "#sqlite":
        print("Using SQLite backend")
        conn = sqlite3.connect(DB_CONFIG["database"])
        conn.row_factory = sqlite3.Row
        return conn
    else:  # mysql
        return mysql.connector.connect(**DB_CONFIG)


def get_cursor(conn, dictionary=False):
    if DB_BACKEND == "#sqlite":
        return conn.cursor()
    else:  # mysql
        return conn.cursor(dictionary=dictionary)
