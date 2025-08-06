CREATE TABLE scraped_pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url TEXT NOT NULL,
    fetched_at DATETIME NOT NULL,
    title TEXT,
    content LONGTEXT,
    status_code INT,
    hash TEXT,
    error_message TEXT
);
