CREATE TABLE robots_rules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    domain VARCHAR(255) NOT NULL UNIQUE,
    user_agent VARCHAR(255) DEFAULT 'MyScraperBot',
    disallow TEXT,
    allow TEXT,
    crawl_delay INT,
    fetched_at DATETIME,
    expires_at DATETIME
);
