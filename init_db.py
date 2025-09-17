from models import get_connection


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS scraped_pages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        url TEXT NOT NULL,
        url_hash CHAR(64) NOT NULL UNIQUE,
        title TEXT,
        content MEDIUMTEXT,
        referrer TEXT,
        status_code INT,
        hash CHAR(64),
        error_message TEXT,
        processed BOOLEAN,
        method VARCHAR(10),
        payload TEXT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    )
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    init_db()
