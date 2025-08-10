from datetime import datetime
import mysql.connector
from config import DB_CONFIG


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
        }


def save_page_to_db(page):
    """スクレイピング結果をデータベースに保存"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO scraped_pages 
            (url, referrer, fetched_at, title, content, status_code, hash, 
             error_message, processed) 
            VALUES (%(url)s, %(referrer)s, %(fetched_at)s, %(title)s, 
                    %(content)s, %(status_code)s, %(hash)s, 
                    %(error_message)s, %(processed)s)
            ON DUPLICATE KEY UPDATE
            referrer = VALUES(referrer),
            fetched_at = VALUES(fetched_at),
            title = VALUES(title),
            content = VALUES(content),
            status_code = VALUES(status_code),
            hash = VALUES(hash),
            error_message = VALUES(error_message),
            processed = VALUES(processed)
        """
        cursor.execute(sql, page.to_dict())
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def get_unprocessed_page():
    """未処理のページを1件取得"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT * FROM scraped_pages 
            WHERE processed = FALSE 
            LIMIT 1
        """
        )
        row = cursor.fetchone()
        return row
    finally:
        cursor.close()
        conn.close()


def mark_page_as_processed(url, error_message=None):
    """ページを処理済みとしてマーク"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE scraped_pages SET processed = TRUE, error_message = %s WHERE url = %s",
            (error_message, url),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
