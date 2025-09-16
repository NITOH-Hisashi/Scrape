from bs4 import BeautifulSoup
from link_extractor import extract_links, normalize_url, extract_title
from models import ScrapedPage, save_page_to_db, get_unprocessed_urls


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
    links = extract_links(soup, source_url="http://example.com")
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
    links = extract_links(soup, source_url="http://example.com")
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
    links = extract_links(soup, source_url="http://example.com")
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
    links = extract_links(soup, source_url="http://example.com")

    # 相対パスは base_url と結合されて含まれる
    assert ("http://example.com/page1.html", "Relative") in links

    # 外部リンクは仕様上返らないことを確認
    assert all("other.com" not in url for url, _ in links)


def test_extract_links_empty_html():
    html = ""
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(soup, source_url="http://example.com")
    assert links == []


def test_save_and_retrieve_links():
    page = ScrapedPage(
        url="https://example.com/test",
        title="Test Page",
        content="",
        referrer=None,
        status_code=None,
        hash_value=None,
        error_message=None,
        processed=False,
        method="GET",
        payload=None,
    )
    save_page_to_db(page)

    urls = get_unprocessed_urls()
    assert "https://example.com/test" in urls


def test_extract_links_with_base_url():
    html = """
    <html>
        <body>
            <a href="/relative/path">Relative Link</a>
            <a href="http://external.com/absolute/path">Absolute Link</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(
        soup, source_url="http://example.com", target_base_url="http://example.com"
    )

    # ベースURLに一致する相対リンクが含まれることを確認
    assert ("http://example.com/relative/path", "Relative Link") in links

    # 外部リンクは仕様上返らないことを確認
    assert all("external.com" not in url for url, _ in links)


def test_extract_links_with_different_base_url():
    html = """
    <html>
        <body>
            <a href="/relative/path">Relative Link</a>
            <a href="http://external.com/absolute/path">Absolute Link</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(
        soup, source_url="http://example.com", target_base_url="http://different.com"
    )

    # ベースURLが異なるため、相対リンクは含まれないことを確認
    assert all("example.com" not in url for url, _ in links)

    # 外部リンクは仕様上返らないことを確認
    assert all("external.com" not in url for url, _ in links)


def test_extract_links_with_no_base_url():
    html = """
    <html>
        <body>
            <a href="/relative/path">Relative Link</a>
            <a href="http://external.com/absolute/path">Absolute Link</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(soup, source_url="http://example.com")

    # ベースURLが指定されていない場合、相対リンクは含まれることを確認
    assert ("http://example.com/relative/path", "Relative Link") in links

    # 外部リンクは仕様上返らないことを確認
    assert all("external.com" not in url for url, _ in links)


def test_normalize_url():
    url = "http://example.com/path/to/page?query=123&ref=abc"
    normalized = normalize_url(url)
    assert normalized == "http://example.com/path/to/page"


def test_extract_title():
    html = """
    <html>
        <head>
            <title>Test Title</title>
        </head>
        <body>
            <h1>Header</h1>
        </body>
    </html>
    """
    title = extract_title(html)
    assert title == "Test Title"


def test_extract_title_no_title():
    html = """
    <html>
        <head>
        </head>
        <body>
            <h1>Header</h1>
        </body>
    </html>
    """
    title = extract_title(html)
    assert title is None


def test_extract_title_empty_html():
    html = ""
    title = extract_title(html)
    assert title is None


def test_extract_title_malformed_html():
    html = "<html><head><title>Unclosed Title</title><body></body></html>"
    title = extract_title(html)
    assert title == "Unclosed Title"


def test_extract_title_whitespace():
    html = """
    <html>
        <head>
            <title>   Title with Whitespace   </title>
        </head>
        <body>
            <h1>Header</h1>
        </body>
    </html>
    """
    title = extract_title(html)
    assert title == "Title with Whitespace".strip()


def test_extract_title_non_html():
    html = "Just some text without HTML tags"
    title = extract_title(html)
    assert title is None
