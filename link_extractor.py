from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

def is_under_base(url, base_url):
    """URLがベースURL配下かどうかをチェック"""
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return parsed_url.netloc == parsed_base.netloc and \
           parsed_url.path.startswith(parsed_base.path)

def extract_links(soup, base_url):
    """BeautifulSoupオブジェクトからリンクを抽出"""
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = urljoin(base_url, href)
        if is_under_base(full_url, base_url):
            title = a.get_text(strip=True)
            # 画像がアンカー内にある場合
            img = a.find('img')
            if img:
                alt = img.get('alt') or img.get('title') or ''
                title = title or alt
            links.append((full_url, title))
    return links

def extract_links(soup: BeautifulSoup, base_url: str) -> list[tuple[str, str]]:
    links = []

    # <a> タグの処理
    for a_tag in soup.find_all("a", href=True):
        href = normalize_url(a_tag["href"])
        text = a_tag.get_text(strip=True)
        full_url = urljoin(base_url, href)
        links.append((full_url, text))

    # <img> タグの処理（alt属性をテキストとして使用）
    for img_tag in soup.find_all("img", src=True):
        src = normalize_url(img_tag["src"])
        alt = img_tag.get("alt", "")
        full_url = urljoin(base_url, src)
        links.append((full_url, alt))

    return links

def normalize_url(url):
    """URLを正規化（クエリパラメータの削除など）"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
