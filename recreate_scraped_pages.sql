-- 既存テーブルを削除（データは全て消えます）
DROP TABLE IF EXISTS scraped_pages;

-- 新しいテーブルを作成
CREATE TABLE scraped_pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url TEXT NOT NULL, -- 実際に取得したページのURL
    referrer TEXT, -- リンク元のURL（任意）
    method VARCHAR(10) NOT NULL DEFAULT 'GET', -- HTTPメソッド（GET/POSTなど）
    payload JSON DEFAULT NULL, -- POSTデータなどをJSON形式で保存
    fetched_at DATETIME, -- 取得日時
    title TEXT, -- ページタイトル（最初に取得したものを保持）
    content LONGTEXT, -- ページ本文
    status_code INT, -- HTTPステータスコード
    hash TEXT, -- 内容のハッシュ値（SHA-256など）
    error_message TEXT, -- エラー内容（取得失敗時）
    processed BOOLEAN DEFAULT FALSE, -- 取得済みかどうかのフラグ
    UNIQUE KEY uniq_url (url(255)) -- URLをユニーク化（先頭255文字）
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
