CREATE TABLE scraped_pages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    url TEXT NOT NULL,                          -- 実際に取得したページのURL
    referrer TEXT,                              -- リンク元のURL（任意）
    method VARCHAR(10) NOT NULL DEFAULT 'GET',  -- HTTPメソッド（GET/POSTなど）
    payload JSON DEFAULT NULL,                  -- POSTデータなどをJSON形式で保存
    fetched_at DATETIME,                        -- 取得日時
    title TEXT,                                 -- ページタイトル
    content LONGTEXT,                           -- ページ本文
    status_code INT,                            -- HTTPステータスコード
    hash TEXT,                                  -- 内容のハッシュ値（SHA-256など）
    error_message TEXT,                         -- エラー内容（取得失敗時）
    processed BOOLEAN DEFAULT FALSE             -- 取得済みかどうかのフラグ
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
