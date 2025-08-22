# Scrape Webスクレイピングツール

効率的で安全なWebスクレイピングを実現するPythonツールセットです。robots.txtの規則を遵守し、重複チェックや再帰的なリンク抽出機能を備えています。

## 主な機能

- 🤖 robots.txtの自動解析と遵守
- 📊 MySQLへのデータ自動保存
- 🔗 インテリジェントなリンク抽出（画像alt属性の解析含む）
- 🔄 コンテンツの重複チェック（SHA-256ハッシュによる）
- 🌲 再帰的なクローリング機能
- ⚠️ 包括的なエラー処理とログ記録

## プロジェクト構成

- `config.py`: データベース設定
- `models.py`: データモデルとデータベース操作
- `robots_handler.py`: robots.txtの取得と解析
- `link_extractor.py`: リンクの抽出と解析
- `scraper.py`: メインのスクレイピング処理

## セットアップ

### 必要環境

- Python 3.x
- MySQL 5.7以上 または MariaDB 10.x以上

```bash
sudo apt install python3-pip
sudo apt install python3.12-venv
python3 -m venv venv
source venv/bin/activate  # Windowsなら venv\\Scripts\\activate
```

### パッケージのインストール

```bash
pip install -r requirements.txt
```

#### パッケージを追加したときに `requirements.txt` を更新する

```bash
pip freeze > requirements.txt
```

### データベースの準備

1. MySQLにデータベースを作成：
```bash
mysql -u root -h localhost -p
```
```sql
CREATE DATABASE scraping_db;
USE scraping_db;
GRANT all ON scraping_db.* TO 'your_user'@'localhost';
ALTER USER 'your_user'@'localhost' IDENTIFIED BY 'your_password';
```

2. 必要なテーブルを作成：
```bash
mysql -u your_user -p scraping_db < schema/scraped_pages.sql
mysql -u your_user -p scraping_db < schema/robots_rules.sql
```

## データベース設定

`config.py`にデータベース接続情報を設定します：

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'scraping_db'
}
```

## 使用方法

### スクレイピングの実行

基本的な実行：
```bash
python scraper.py
```

オプションの指定：
```bash
# カスタムUser-agentを指定して実行
python scraper.py --user-agent "CustomBot/1.0"
```

### スクレイピング対象の追加

スクレイピング対象のURLをデータベースに追加します：

```sql
INSERT INTO scraped_pages (url, processed) VALUES ('https://example.com', FALSE);
```

### 推奨開発環境
- VisualStudioCode
  https://azure.microsoft.com/ja-jp/products/visual-studio-code
- A5:SQL Mk-2
  https://a5m2.mmatsubara.com/
  
## データベーススキーマ

### scraped_pages テーブル

- `url`: スクレイピング対象のURL（主キー）
- `referrer`: リンク元のURL
- `fetched_at`: 取得日時
- `title`: ページタイトルまたはリンクテキスト
- `content`: ページのHTML内容
- `status_code`: HTTPステータスコード
- `hash`: コンテンツのハッシュ値
- `error_message`: エラー情報（存在する場合）
- `processed`: 処理済みフラグ

### robots_rules テーブル

- `domain`: ドメイン名（主キー）
- `user_agent`: User-agent文字列
- `disallow`: 禁止パターン（改行区切り）
- `allow`: 許可パターン（改行区切り）
- `crawl_delay`: クロール間隔（秒）
- `fetched_at`: 取得日時
- `expires_at`: 有効期限（24時間）

## 注意事項

- 対象サイトのrobots.txtを自動的に確認・遵守します
- クロール間隔はrobots.txtの指定に従います
- データの利用は各サイトの利用規約に従ってください
- エラー発生時もデータベースに記録が残ります

## エラー対処

1. データベースエラー
   - MySQLサービスの起動確認
   - ユーザー権限の確認
   - 接続情報の確認

2. ネットワークエラー
   - タイムアウト値の調整（デフォルト: 10秒）
   - プロキシ設定の確認
   - ファイアウォール設定の確認

---
## ✅ テストの実行方法

### 1. 必要な環境の準備
- Python 3.x
- `requests`, `beautifulsoup4`, `mysql-connector-python` などの依存パッケージをインストール：
```bash
pip install -r requirements.txt
```

### 2. データベースの準備（MySQL）
```bash
mysql -u root -h localhost -p
```
```sql
CREATE DATABASE scraping_db;
USE scraping_db;
GRANT all ON scraping_db.* TO 'your_user'@'localhost';
ALTER USER 'your_user'@'localhost' IDENTIFIED BY 'your_password';
```

- スキーマのインポート
```bash
mysql -u your_user -p scraping_db < schema/scraped_pages.sql
mysql -u your_user -p scraping_db < schema/robots_rules.sql
```

### 3. DB接続設定（`config.py`）
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'scraping_db'
}
```

### 4. テストの実行
テストファイルは `tests/` ディレクトリにあり、`pytest` で実行可能です：

```bash
PYTHONPATH=. pytest
```

特定のテストだけを実行したい場合：
```bash
pytest tests/test_scrape.py
```

### 5. モックを使ったテスト例
`test_scrape_failure(mock_get)` という関数が確認されており、`requests.get` をモックして失敗ケースを検証しています。`pytest-mock` が必要な場合はインストールしてください：

```bash
pip install pytest-mock
```

---

## 参考資料

- [Requests ドキュメント](https://requests.readthedocs.io/ja/latest/)
- [BeautifulSoup ドキュメント](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [MySQLコネクタ/Python](https://dev.mysql.com/doc/connector-python/en/)
- [MariaDBセットアップガイド](https://qiita.com/nanbuwks/items/c98c51744bd0f72a7087) https://qiita.com/nanbuwks/items/c98c51744bd0f72a7087

