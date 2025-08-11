import requests
from bs4 import BeautifulSoup
import hashlib
import time
from models import (
    ScrapedPage,
    save_page_to_db,
    get_unprocessed_page,
    mark_page_as_processed,
)
from link_extractor import extract_links
from robots_handler import check_robots_rules


def get_hash(text):
    """ハッシュ値を生成"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def should_scrape(url, user_agent):
    """robots.txt に基づくスクレイプ可否と遅延処理"""
    allowed, delay = check_robots_rules(url, user_agent)
    if not allowed:
        mark_page_as_processed(url, "Blocked by robots.txt")
        return False
    if delay > 0:
        time.sleep(delay)
    return True


def scrape_page(url, referrer=None):
    """HTML取得と ScrapedPage の生成"""
    try:
        headers = {"Referer": referrer} if referrer else {}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else ""
        content = response.text
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


def fetch_post_content(url, data, referrer=None, headers=None):
    """POSTリクエストでHTMLを取得し ScrapedPage を生成"""
    try:
        headers = headers or {}
        if referrer:
            headers["Referer"] = referrer
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else ""
        content = response.text
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
    soup = BeautifulSoup(page.content, "html.parser")
    links = extract_links(soup, page.url)
    for link_url, link_title in links:
        new_page = ScrapedPage(url=link_url, referrer=page.url, title=link_title)
        save_page_to_db(new_page)


def process_single_page(row, user_agent):
    """1ページ分の処理をまとめる"""
    url = row["url"]
    if not should_scrape(url, user_agent):
        print(f"Skipping {url} (blocked by robots.txt)")
        return
    page = scrape_page(url, row.get("referrer"))
    save_page_to_db(page)
    if page.error_message is None:
        extract_and_save_links(page)
    mark_page_as_processed(url)


def process_pages(user_agent="MyScraperBot"):
    """未処理ページを順に処理"""
    while True:
        row = get_unprocessed_page()
        if not row:
            break
        process_single_page(row, user_agent)


def main():
    """CLI引数を処理してスクレイピングを開始"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Web scraping tool with robots.txt compliance"
    )
    parser.add_argument(
        "--user-agent",
        default="MyScraperBot",
        help="User agent string to use for requests (default: MyScraperBot)",
    )
    args = parser.parse_args()
    print(f"Starting scraper with User-Agent: {args.user_agent}")
    process_pages(user_agent=args.user_agent)


if __name__ == "__main__":
    main()
