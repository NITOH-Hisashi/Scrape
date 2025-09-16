from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import argparse
from html_fetcher import fetch_html  # Playwright/requests切り替え関数
from models import ScrapedPage, save_page_to_db
from typing import Optional


def is_under_base(url: str, base_url: str) -> bool:
    """URLがベースURL配下かどうかをチェック"""
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return parsed_url.netloc == parsed_base.netloc and parsed_url.path.startswith(
        parsed_base.path
    )


def extract_links(
    soup: BeautifulSoup, source_url: str, target_base_url: Optional[str] = None
) -> list[tuple[str, str]]:
    """BeautifulSoupオブジェクトからリンクを抽出（ベースURL指定可能）"""
    links = []

    # <a> タグの処理
    for a_tag in soup.find_all("a", href=True):
        full_url = normalize_url(urljoin(source_url, a_tag["href"]))  # type: ignore

        # 外部リンクやベースURL配下でないリンクはスキップ
        if target_base_url:
            if not is_under_base(full_url, target_base_url):
                continue
        else:
            if not is_under_base(full_url, source_url):
                continue

        text = a_tag.get_text(strip=True)

        # <img> タグの処理（alt属性をテキストとして使用）
        img_tag = a_tag.find("img", attrs={"alt": True})  # type: ignore
        if img_tag:
            text += " " + img_tag.get("alt", "").strip()  # type: ignore
        img_tag = a_tag.find("img", attrs={"title": True})  # type: ignore
        if img_tag:
            text += " " + img_tag.get("title", "").strip()  # type: ignore
        text = " ".join(text.split())  # 余分な空白を削除

        links.append((full_url.strip(), text))

    return links


def normalize_url(url: str) -> str:
    """URLを正規化（クエリパラメータの削除など）"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def extract_title(html_content: str) -> Optional[str]:
    """HTMLからタイトルを抽出"""

    try:

        soup = BeautifulSoup(html_content, "html.parser")

        if soup.title and soup.title.string:

            return soup.title.string.strip()

    except Exception:

        pass

    return None


def extract_and_save_links(
    source_url: str, target_base_url: Optional[str] = None, use_playwright: bool = False
):
    """リンク抽出とScrapedPage保存処理"""
    html = fetch_html(source_url, use_playwright)
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(soup, source_url, target_base_url)

    for url, title in links:
        page = ScrapedPage(
            url=url,
            title=title,
            content="",  # 本文は未取得
            referrer=source_url,
            status_code=None,
            hash_value=None,
            error_message=None,
            processed=False,
            method="GET",
        )
        save_page_to_db(page)
    return links


def main():
    parser = argparse.ArgumentParser(description="リンク抽出ツール")
    parser.add_argument("--source", required=True, help="リンク抽出元のURL")
    parser.add_argument(
        "--base",
        required=False,
        help="抽出対象のベースURL（指定しない場合はsourceと同じ）",
    )
    args = parser.parse_args()

    source_url = args.source
    base_url = args.base if args.base else source_url

    links = extract_and_save_links(
        source_url, target_base_url=base_url, use_playwright=True
    )

    for url, text in links:
        print(f"{url} | {text}")
