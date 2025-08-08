CREATE TABLE scraped_pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url TEXT NOT NULL,               -- 実際に取得したページのURL
    referrer TEXT,                   -- リンク元のURL（任意）
    fetched_at DATETIME NOT NULL,    -- 取得日時
    title TEXT,                      -- ページタイトル（リンク元アンカー文字列）
    content LONGTEXT,                -- ページ本文
    status_code INT,                 -- HTTPステータスコード
    hash TEXT,                       -- 内容のハッシュ値
    error_message TEXT               -- エラー内容（取得失敗時）
);
