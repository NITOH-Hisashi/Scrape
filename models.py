from datetime import datetime
import mysql.connector
from config import DB_CONFIG
import json


class ScrapedPage:
    def __init__(
        self,
        url,
        referrer=None,
        title=None,
        content=None,
        status_code=None,
        hash_value=None,
        error_message=None,
        method="GET",
        payload=None,
    ):
        self.url = url
        self.referrer = referrer
        self.fetched_at = datetime.now()
        self.title = title
        self.content = content
        self.status_code = status_code
        self.hash = hash_value
        self.error_message = error_message
        self.processed = False
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
        }


def save_page_to_db(page):
    """スクレイピング結果をデータベースに保存（POST対応）"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        # 値の型を安全に変換
        page_dict = page.to_dict()
        if page_dict.get("hash") is not None and not isinstance(page_dict["hash"], str):
            # bytesやその他の型を文字列化（例: SHA256のbytes → hex文字列）
            page_dict["hash"] = (
                page_dict["hash"].hex()
                if hasattr(page_dict["hash"], "hex")
                else str(page_dict["hash"])
            )

        sql = """
            INSERT INTO scraped_pages (
                url,
                referrer,
                fetched_at,
                title,
                content,
                status_code,
                `hash`,
                error_message,
                processed,
                method,
                payload
            )
            VALUES (
                %(url)s,
                %(referrer)s,
                %(fetched_at)s,
                %(title)s,
                %(content)s,
                %(status_code)s,
                %(hash)s,
                %(error_message)s,
                %(processed)s,
                %(method)s,
                %(payload)s
            )
            ON DUPLICATE KEY UPDATE
                referrer = VALUES(referrer),
                fetched_at = VALUES(fetched_at),
                title = VALUES(title),
                content = VALUES(content),
                status_code = VALUES(status_code),
                `hash` = VALUES(`hash`),
                error_message = VALUES(error_message),
                processed = VALUES(processed),
                method = VALUES(method),
                payload = VALUES(payload)
        """
        cursor.execute(sql, page_dict)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_unprocessed_page():
    """未処理のページを1件取得（POST対応）"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
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
        row = cursor.fetchone()
        if row:
            payload = json.loads(row.get("payload") or "{}") if row["payload"] else {}
            return {
                "url": row["url"],
                "referrer": row["referrer"],
                "method": row.get("method", "GET").upper(),
                "payload": payload,
            }
        return None
    finally:
        cursor.close()
        conn.close()


def mark_page_as_processed(url, error_message=None):
    """ページを処理済みとしてマーク"""
    conn = mysql.connector.connect(**DB_CONFIG)
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
