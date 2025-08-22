from models import ScrapedPage, save_page_to_db
import hashlib


def main():
    # ダミーのページデータを作成
    url = "https://example.com/test"
    content = "<html><body><h1>Hello World</h1></body></html>"

    # SHA256ハッシュを生成（bytes型でテスト）
    hash_bytes = hashlib.sha256(content.encode("utf-8")).digest()

    page = ScrapedPage(
        url=url,
        referrer="https://example.com",
        title="Test Page",
        content=content,
        status_code=200,
        hash_value=hash_bytes,  # bytes型を渡して型変換が効くか確認
        error_message=None,
        method="GET",
        payload={"test": True},
    )

    try:
        save_page_to_db(page)
        print("✅ データベースへの保存に成功しました")
    except Exception as e:
        print("❌ 保存中にエラーが発生しました:", e)


if __name__ == "__main__":
    main()
