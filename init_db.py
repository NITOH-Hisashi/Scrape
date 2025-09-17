from models import get_connection


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS scraped_pages (
        id INT AUTO_INCREMENT PRIMARY KEY,
        url VARCHAR(2083) UNIQUE,
        title TEXT,
        content MEDIUMTEXT,
        referrer VARCHAR(2083),
        status_code INT,
        hash VARCHAR(64),
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
