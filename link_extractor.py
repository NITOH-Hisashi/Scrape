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
        full_url = normalize_url(urljoin(base_url, a_tag["href"]))  # type: ignore

        # 外部リンクやベースURL配下でないリンクはスキップ
        if not is_under_base(full_url, base_url):
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


def normalize_url(url):
    """URLを正規化（クエリパラメータの削除など）"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
