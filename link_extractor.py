from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup


def is_under_base(url, base_url):
    """URLがベースURL配下かどうかをチェック"""
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return parsed_url.netloc == parsed_base.netloc and parsed_url.path.startswith(
        parsed_base.path
    )


def extract_links(soup: BeautifulSoup, base_url: str) -> list[tuple[str, str]]:
    """BeautifulSoupオブジェクトからリンクを抽出"""
    links = []

    # <a> タグの処理
    for a_tag in soup.find_all("a", href=True):
        raw_href = a_tag["href"]
        full_url = normalize_url(urljoin(base_url, raw_href))
        text = a_tag.get_text(strip=True)
        links.append((full_url, text))

    # <img> タグの処理（alt属性をテキストとして使用）
    for img_tag in soup.find_all("img", src=True):
        raw_src = img_tag["src"]
        full_url = normalize_url(urljoin(base_url, raw_src))
        alt = img_tag.get("alt", "")
        links.append((full_url, alt))

    return links


def normalize_url(url):
    """URLを正規化（クエリパラメータの削除など）"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
