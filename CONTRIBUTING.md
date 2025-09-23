# Contributing Guide

## 依存関係管理
- 新しいパッケージを追加した場合は必ず `requirements.txt` を更新してください
- 例:
    `pip freeze > requirements.txt`

## コードスタイル
- black を用いてコードを自動整形してください
- flake8 で静的解析を行い、警告が出ない状態を維持してください

### 推奨開発環境
- VisualStudioCode
  https://azure.microsoft.com/ja-jp/products/visual-studio-code
- A5:SQL Mk-2
  https://a5m2.mmatsubara.com/

### ドキュメントのフォーマット
```bash
black .
flake8 .
```
  
## テスト
- すべての PR は pytest が通ることを確認してください
- CI では ENV=test を利用し、SQLite での再現性を担保します
- MySQL 互換性も定期的に確認してください

## ブランチ運用
- 開発は Development ブランチで行ってください
- main ブランチへの PR は必ずレビューを経てマージしてください

## テーブル設計変更の時にテーブルを作り直す方法
```bash
mysql -u your_user -p scraping_db < recreate_scraped_pages.sql
```

## 参考資料

- [Requests ドキュメント](https://requests.readthedocs.io/ja/latest/)
- [BeautifulSoup ドキュメント](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [MySQLコネクタ/Python](https://dev.mysql.com/doc/connector-python/en/)
- [MariaDBセットアップガイド](https://qiita.com/nanbuwks/items/c98c51744bd0f72a7087) https://qiita.com/nanbuwks/items/c98c51744bd0f72a7087
- [MySQL | 新しいパスワードを設定する(SET PASSWORD 文、ALTER USER文)](https://www.javadrive.jp/mysql/user/index2.html) https://www.javadrive.jp/mysql/user/index2.html
