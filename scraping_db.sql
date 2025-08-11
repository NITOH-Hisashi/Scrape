CREATE DATABASE scraping_db;
USE scraping_db;
source robots_rules.sql
source scraped_pages.sql;

-- テーブル変更SQL（未追加なら）
ALTER TABLE scraped_pages ADD COLUMN method TEXT DEFAULT 'GET';
ALTER TABLE scraped_pages ADD COLUMN payload TEXT;
