from models import ScrapedPage, save_page_to_db
import hashlib


# このスクリプトは、ScrapedPage オブジェクトを作成し、データベースに保存する方法を示します。
# ページが正しく保存されることを確認するためのテストケースが含まれています。
# ハッシュ値はバイトオブジェクトとして生成され、保存前に文字列に変換されます。
# 注意：このスクリプトは、データベース接続とテーブル構造が既に正しく設定されていることを前提としています。
# 問題が発生した場合は、データベースの設定とScrapedPageモデルの定義に不一致がないかご確認ください。
#
# スクリプトには、例を実行するためのメイン関数も含まれており、直接実行可能です。
# $ python -m tests.test_save_page
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
