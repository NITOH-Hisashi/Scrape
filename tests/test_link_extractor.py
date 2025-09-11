from bs4 import BeautifulSoup
from link_extractor import extract_links


def test_extract_links_basic():
    html = """
    <html>
        <body>
            <a href="http://example.com/page1">Page 1</a>
            <a href="/page2">Page 2</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(soup, base_url="http://example.com")
    assert isinstance(links, list)
    assert ("http://example.com/page1", "Page 1") in links
    assert ("http://example.com/page2", "Page 2") in links


def test_extract_links_img_alt():
    html = """
    <html>
        <body>
            <a href="http://example.com/image">
                <img src="img.jpg" alt="Alt Text" />
            </a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(soup, base_url="http://example.com")
    # ↓ ここを return → assert に変更
    assert isinstance(links, list)
    assert ("http://example.com/image", "Alt Text") in links


def test_extract_links_no_href():
    html = """
    <html>
        <body>
            <a>Broken Link</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(soup, base_url="http://example.com")
    assert links == []


def test_extract_links_relative_and_absolute():
    html = """
    <html>
        <body>
            <a href="page1.html">Relative</a>
            <a href="http://other.com/page2">Absolute</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(soup, base_url="http://example.com")

    # 相対パスは base_url と結合されて含まれる
    assert ("http://example.com/page1.html", "Relative") in links

    # 外部リンクは仕様上返らないことを確認
    assert all("other.com" not in url for url, _ in links)
