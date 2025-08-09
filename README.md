# Scrape Webスクレイピングツール

効率的で安全なWebスクレイピングを実現するPythonツールセットです。robots.txtの規則を遵守し、重複チェックや更新確認機能を備えています。

## 主な機能

- 🤖 robots.txtの自動解析と遵守
- 📊 MySQLへのデータ自動保存
- 🔗 インテリジェントなリンク抽出（画像alt属性の解析含む）
- 🔄 コンテンツの重複チェック（SHA-256ハッシュによる）
- ⌚ If-Modified-Since による更新確認
- 🌲 再帰的なクローリング機能
- ⚠️ 包括的なエラー処理とログ記録

## セットアップ

### 必要環境

- Python 3.x
- MySQL 5.7以上 または MariaDB 10.x以上

### パッケージのインストール

```bash
pip install requests beautifulsoup4 mysql-connector-python
```

### データベースの準備

1. MySQLにデータベースを作成：
```sql
CREATE DATABASE scraping_db;
USE scraping_db;
```

2. 必要なテーブルを作成：
```bash
mysql -u your_user -p scraping_db < schema/scraped_pages.sql
mysql -u your_user -p scraping_db < schema/robots_rules.sql
```

## 基本的な使い方

### 単一ページのスクレイピング

```python
from scrape import scrape, save_to_mysql

# 基本的なスクレイピング
result = scrape('https://example.com')
save_to_mysql(result)
```

### 再帰的なクローリング

```python
from scrape import crawl_and_store

# ドメイン配下を再帰的にクロール
base_url = 'https://example.com'
crawl_and_store(base_url)
```

### robots.txt対応のスクレイピング

```python
from scrape import is_allowed_by_robots, scrape

url = 'https://example.com/page'
if is_allowed_by_robots(url):
    result = scrape(url)
    save_to_mysql(result)
```

## 高度な機能

### 更新チェック付きフェッチ

```python
from scrape import fetch_if_modified
from datetime import datetime

last_fetch = datetime.now()
response = fetch_if_modified('https://example.com', last_fetch)
if response.status_code == 304:
    print("コンテンツは更新されていません")
```

### リンク抽出

```python
from scrape import extract_links
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_content, 'html.parser')
links = extract_links(soup, 'https://example.com')
for url, title in links:
    print(f"{title}: {url}")
```

## 設定

データベース接続情報は以下の形式で設定します：

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'scraping_db'
}
```

## 注意事項

- 対象サイトのrobots.txtを必ず確認・遵守してください
- クロール間隔は適切に設定してください（デフォルト: 1リクエスト/秒）
- データの利用は各サイトの利用規約に従ってください
- SSLエラーが発生する場合は証明書の設定を確認してください

## エラー対処

1. データベースエラー
   - MySQLサービスの起動確認
   - ユーザー権限の確認
   - 接続情報の確認

2. ネットワークエラー
   - タイムアウト値の調整
   - プロキシ設定の確認
   - ファイアウォール設定の確認

## ライセンス

MIT License

## 参考資料

- [Requests ドキュメント](https://requests.readthedocs.io/ja/latest/)
- [BeautifulSoup ドキュメント](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [MySQLコネクタ/Python](https://dev.mysql.com/doc/connector-python/en/)
- [MariaDBセットアップガイド](https://qiita.com/nanbuwks/items/c98c51744bd0f72a7087) https://qiita.com/nanbuwks/items/c98c51744bd0f72a7087

