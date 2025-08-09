# AIコーディングエージェント向け説明書

このプロジェクトは、robots.txtを遵守した安全なWebスクレイピングを実現するPythonツールセットです。

## アーキテクチャ概要

### コアコンポーネント
1. **スクレイピングエンジン** (`scrape.py`)
   - 単一ページの取得
   - コンテンツのハッシュ化
   - リンク抽出
   - エラーハンドリング

2. **robots.txt管理** (`fetch_and_store_robots.py`)
   - robots.txtの取得と解析
   - クロール規則のデータベース保存
   - アクセス可否判定

3. **データストア** (MySQL)
   - `scraped_pages`: スクレイプされたコンテンツの保存
   - `robots_rules`: robots.txtのルール保存

### データフロー
1. robots.txtの取得・解析 → DBへの保存
2. URLのクロール許可確認 → スクレイピング実行
3. コンテンツとメタデータの保存 → リンクの抽出 → 新規URLの登録

## 開発ワークフロー

### セットアップ
```python
# データベース設定 (config.py)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password',
    'database': 'scraping_db'
}
```

### デバッグのベストプラクティス
- エラーメッセージは `error_message` カラムに保存
- URLごとの処理状態は `processed` フラグで管理
- ハッシュ値による重複チェックを活用

## プロジェクト固有の規則

1. **エラーハンドリング**
   - すべてのネットワークリクエストは例外処理必須
   - タイムアウト値は10秒固定 (`timeout=10`)
   - エラー発生時もDBに記録を残す

2. **データベース操作**
   - トランザクション管理必須
   - 重複処理を避けるためのUPSERT使用
   - 大量テキストはLONGTEXT型で保存

3. **リンク処理**
   - 相対パスは絶対URLに変換
   - 画像のalt/title属性も保存
   - ベースURL外のリンクは除外

## 統合ポイント

1. **外部依存関係**
   ```python
   requests==2.31.0
   beautifulsoup4==4.12.2
   mysql-connector-python==8.2.0
   ```

2. **コンポーネント間通信**
   - `scrape.py` ⇔ `fetch_and_store_robots.py`: URLの許可確認
   - データベースを介したイベント管理（`processed`フラグ）
   - ハッシュ値によるコンテンツ重複検出
