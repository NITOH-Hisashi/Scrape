# Scrape Webスクレイピングツール

効率的で安全な Web スクレイピングを実現する Python ツールセットです。  
本プロジェクトは **環境変数管理の徹底** と **SQLite/CI 対応** を重視しており、  
ローカル開発・テスト・CI/CD での再現性と環境分離を保証します。  

---

## 🎯 設計思想（開発者向け）

本プロジェクトは「**再現性・環境分離・責務分離**」を最重要視しています。  

- **再現性**  
  - ローカル・テスト・CI/CD で同じコードが同じ挙動をすることを保証  
  - DB バックエンド（MySQL/SQLite）を環境変数で切り替え可能  
  - `.env.local` / `.env.test` による設定分離で、環境依存の不具合を最小化  

- **環境分離**  
  - `ENV=local` → `environment/.env.local`  
  - `ENV=test` → `environment/.env.test`  
  - CI/CD では `ENV=test` を明示的にセットし、SQLite を利用して高速・安全にテスト  

- **責務分離**  
  - `config.py` : 環境変数と DB 設定  
  - `models.py` : データモデルと DB 操作  
  - `robots_handler.py` : robots.txt の取得と解析  
  - `link_extractor.py` : リンク抽出と解析  
  - `scraper.py` : スクレイピングの実行フロー  
  - 各モジュールは単一責務を意識し、テスト可能性を高めています  

- **Playwright 判定**  
  - 環境変数 `USE_PLAYWRIGHT_PATTERNS` により、動的ページを Playwright で取得するかを制御  
  - 正規表現やドメイン指定で柔軟に制御可能  
  - 例:  
    ```env
    USE_PLAYWRIGHT_PATTERNS=example.com,/dynamic/
    ```

---

## 🚀 主な機能
- 🤖 robots.txt の自動解析と遵守  
- 📊 MySQL / SQLite へのデータ保存（環境に応じて切替可能）  
- 🔗 インテリジェントなリンク抽出（画像 alt 属性の解析含む）  
- 🔄 コンテンツの重複チェック（SHA-256 ハッシュ）  
- 🌲 再帰的クロール機能  
- 🎭 Playwright を用いた動的ページ対応  
- ⚠️ 包括的なエラー処理とログ記録  

---

## 📂 プロジェクト構成
```
environment/config.py   # 環境変数・DB 設定
models.py               # データモデルと DB 操作
robots_handler.py       # robots.txt の取得と解析
link_extractor.py       # リンク抽出と解析
scraper.py              # メインのスクレイピング処理
tests/                  # pytest によるテスト
```

## 🛠 セットアップ

### 必要環境
- Python 3.12+
- MySQL 5.7+ / MariaDB 10.x+ または SQLite（テスト用）

```bash
sudo apt install python3-pip python3.12-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ⚙️ 環境変数管理

### ローカル開発
```bash
export ENV=local
```
→ environment/.env.local を読み込む

### テスト/CI
```
export ENV=test
```
→ environment/.env.test を読み込む

### 例: .env.local
```
ENV=local
DATABASE_URL=mysql://your_user:your_password@localhost:3306/scraping_db
USE_PLAYWRIGHT_PATTERNS=example.com,/dynamic/
```

------------------------------------------------------------

## 🗄 データベース準備

### MySQL
```
CREATE DATABASE scraping_db;
CREATE USER 'your_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL ON scraping_db.* TO 'your_user'@'localhost';
```

### SQLite
.env.test に以下を設定するだけで利用可能:
```
DB_BACKEND=sqlite
```

------------------------------------------------------------

## ▶️ 使い方

### スクレイピング実行
```
python scraper.py
```

### オプション例
```
python scraper.py --url https://example.com --user-agent "CustomBot/1.0"
```

------------------------------------------------------------

## ✅ テスト

```
PYTHONPATH=. pytest
```

- DB をモックしたテスト
- Playwright 有効/無効の両ケースをカバー
- CI では SQLite を利用し、MySQL 互換性チェックも実行

------------------------------------------------------------

## ⚠️ 注意事項

- robots.txt を自動で確認・遵守します
- クロール間隔は robots.txt の指定に従います
- データ利用は各サイトの利用規約に従ってください
- エラー発生時も DB に記録が残るため、再現性のあるデバッグが可能です

------------------------------------------------------------

## 📌 開発者向けメモ

- 再現性を担保するため、環境変数は必ず .env.local / .env.test に明示的に記述してください
- 責務分離を守ること：新しい機能を追加する際は既存モジュールの責務を壊さないように設計してください
- テストは CI 前提：SQLite で必ず通ることを確認し、MySQL 互換性も担保してください
