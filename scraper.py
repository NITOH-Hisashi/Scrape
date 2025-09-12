import types
import requests
from bs4 import BeautifulSoup
import hashlib
import time
from urllib.parse import urlparse
from models import (
    ScrapedPage,
    save_page_to_db,
    get_unprocessed_page,
    mark_page_as_processed,
    get_page_counts,
    exists_in_db,
)
from link_extractor import extract_links, extract_title
from robots_handler import check_robots_rules
import argparse
import json
from playwright.sync_api import sync_playwright  # type: ignore
from config import USE_PLAYWRIGHT_PATTERNS


def get_hash(text):
    """ハッシュ値を生成"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def should_scrape(url, user_agent):
    """robots.txt に基づくスクレイプ可否と遅延処理"""
    allowed, delay = check_robots_rules(url, user_agent)
    if not allowed:
        mark_page_as_processed(url, "Blocked by robots.txt")
        return False
    if float(delay) > 0.0:  # type: ignore
        time.sleep(delay)  # type: ignore
    return True


def scrape_page(url: str, referrer: str | None = None) -> ScrapedPage:
    """HTML取得と ScrapedPage の生成"""
    url = (url or "").strip()
    if not url:
        return ScrapedPage(
            url=None, title=None, content="", error_message="URL is empty"
        )
    use_playwright = any(pat in url for pat in USE_PLAYWRIGHT_PATTERNS)

    try:
        if use_playwright:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page_obj = browser.new_page()
                if referrer:
                    page_obj.set_extra_http_headers({"Referer": referrer})
                page_obj.goto(url, wait_until="networkidle")
                content = await_or_call(page_obj.content())
                title = (await_or_call(page_obj.title())) or urlparse(url).netloc
                browser.close()
                status_code = 200
                return ScrapedPage(
                    url=url, title=title, content=content, error_message=None
                )
        else:
            headers = {"Referer": referrer} if referrer else {}
            response = requests.get(url, headers=headers, timeout=10)
            # byte_size = len(response.content)
            # print(f"[DEBUG] Raw content size: {byte_size} bytes")

            response.encoding = response.apparent_encoding
            response.raise_for_status()
            content = response.text or ""

            # バイト数を表示（UTF-8でエンコードした場合）
            # byte_size = len(
            #   content.encode(response.encoding or "utf-8", errors="ignore")
            # )
            # print(f"[DEBUG] {url} の取得サイズ: {byte_size} bytes")

            if content.lstrip().startswith("<?xml"):
                soup = BeautifulSoup(content, features="xml")
            else:
                # print(f"[DEBUG] content(before parse)={repr(content)}")
                soup = BeautifulSoup(content, "html.parser")
                # print(f"[DEBUG] soup.title={soup.title}")
                # print(f"[DEBUG] soup.title.string"
                #      "={soup.title.string if soup.title else None!r}")

            title = extract_title(content) or urlparse(url).netloc
            status_code = response.status_code
        hash_value = get_hash(content)
        return ScrapedPage(
            url=url,
            referrer=referrer,
            title=title,
            content=content,
            status_code=status_code,
            hash_value=hash_value,
            error_message=None,
        )
    except Exception as e:
        return ScrapedPage(
            url=url,
            referrer=referrer,
            title=None,
            content="",
            status_code=None,
            hash_value=None,
            error_message=str(e),
        )


def await_or_call(value):
    """値がawaitableならawaitし、そうでなければそのまま返す"""
    if isinstance(value, types.CoroutineType) or hasattr(value, "__await__"):
        return value.__await__().__next__()
    return value


def fetch_post_content(url, data, referrer=None, headers=None):
    """POSTリクエストでHTMLを取得し ScrapedPage を生成"""
    try:
        headers = headers or {}
        if referrer:
            headers["Referer"] = referrer
        response = requests.post(url, data=data, headers=headers, timeout=10)
        # byte_size = len(response.content)
        # print(f"[DEBUG] Raw content size: {byte_size} bytes")

        response.encoding = response.apparent_encoding
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else ""
        content = response.text

        # バイト数を表示（UTF-8でエンコードした場合）
        # byte_size = len(content.encode(response.encoding or "utf-8", errors="ignore"))
        # print(f"[DEBUG] {url} の取得サイズ: {byte_size} bytes")

        hash_value = get_hash(content)
        return ScrapedPage(
            url=url,
            referrer=referrer,
            title=title,
            content=content,
            status_code=response.status_code,
            hash_value=hash_value,
        )
    except Exception as e:
        return ScrapedPage(url=url, referrer=referrer, error_message=str(e))


def extract_and_save_links(page):
    """リンク抽出と保存"""
    if page.content.lstrip().startswith("<?xml"):
        soup = BeautifulSoup(page.content, features="xml")
    else:
        soup = BeautifulSoup(page.content, "html.parser")
    links = extract_links(soup, page.url)
    for link_url, link_title in links:
        if not exists_in_db(link_url):
            new_page = ScrapedPage(url=link_url, referrer=page.url, title=link_title)
            save_page_to_db(new_page)


def process_single_page(row, user_agent):
    """1ページ分の処理をまとめる"""
    url = row.get("url")
    if not url:
        print(f"[WARN] URLがNoneまたは空のためスキップ: {row}")
        return
    url = row["url"]
    method = row.get("method", "GET").upper()
    payload = row.get("payload", {})  # dict形式を想定

    if not should_scrape(url, user_agent):
        print(f"Skipping {url} (blocked by robots.txt)")
        return

    if method == "POST":
        page = fetch_post_content(url, data=payload, referrer=row.get("referrer"))
    else:
        page = scrape_page(url, row.get("referrer"))

    save_page_to_db(page)
    if page.error_message is None:
        if page.content and page.content.strip():
            extract_and_save_links(page)
            mark_page_as_processed(url)
            print(f"Mark as processed for {url}")
        else:
            # 空コンテンツでも再処理しない場合
            mark_page_as_processed(url)
            print(f"Mark as processed for {url} (empty content)")
    else:
        # エラー時は再処理しないため processed=TRUE にする
        mark_page_as_processed(url)
        print(f"Mark as processed for {url} ({page.error_message})")


def process_pages(user_agent="MyScraperBot"):
    """未処理ページを順に処理"""
    while True:
        row = get_unprocessed_page()
        url = row["url"] if row else None
        if not url:
            break
        process_single_page(row, user_agent)


def main():
    """CLI引数を処理してスクレイピングを開始"""

    parser = argparse.ArgumentParser(
        description="Web scraping tool with robots.txt compliance"
    )
    parser.add_argument(
        "--user-agent",
        default="MyScraperBot",
        help="User agent string to use for requests",
    )
    parser.add_argument("--url", help="Target URL to scrape")
    parser.add_argument("--referrer", help="Referrer URL")
    parser.add_argument(
        "--method", choices=["GET", "POST"], default="GET", help="HTTP method to use"
    )
    parser.add_argument("--payload", type=str, help="POST payload as JSON string")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="全レコードの processed を未処理(FALSE)にリセットしてから実行",
    )

    args = parser.parse_args()

    print(f"Starting scraper with User-Agent: {args.user_agent}")

    if args.reset:
        from models import reset_all_processed

        reset_all_processed()
        print("✅ 全レコードの processed を未処理にリセットしました")

    # 実行前の件数表示
    unprocessed_count, processed_count = get_page_counts()
    print(f"未処理: {unprocessed_count} 件, 処理済み: {processed_count} 件")

    processed_before = processed_count

    if args.url:
        payload_dict = json.loads(args.payload) if args.payload else {}
        row = {
            "url": args.url,
            "referrer": args.referrer,
            "method": args.method,
            "payload": payload_dict,
        }
        process_single_page(row, user_agent=args.user_agent)
        # 最初のURL処理後に未処理ページも続けて処理
        process_pages(user_agent=args.user_agent)
    else:
        process_pages(user_agent=args.user_agent)

    # 実行後の件数表示
    unprocessed_after, processed_after = get_page_counts()
    processed_diff = processed_after - processed_before
    print(f"今回処理した件数: {processed_diff} 件")
    print(f"未処理: {unprocessed_after} 件, 処理済み: {processed_after} 件")


if __name__ == "__main__":
    main()
