from bs4 import BeautifulSoup
from link_extractor import is_under_base, extract_links, normalize_url
from urllib.parse import urljoin


def test_is_under_base():
    base = "http://example.com/path/"
    url_in = "http://example.com/path/page.html"
    url_out = "http://example.com/other/page.html"
    assert is_under_base(url_in, base) == True
    assert is_under_base(url_out, base) == False


def test_extract_links():
    base = "http://example.com/"
    html = '''<html><body>
        <a href="page1.html">Page 1</a>
        <a href="/page2.html">Page 2</a>
        <a href="http://example.org/">External</a>
    </body></html>'''
    soup = BeautifulSoup(html, 'html.parser')
    links = extract_links(soup, base)
    extracted_urls = [link[0] for link in links]
    assert "http://example.com/page1.html" in extracted_urls
    assert "http://example.com/page2.html" in extracted_urls
    # Ensure only URLs under the base are returned
    assert len(extracted_urls) == 2


def test_normalize_url():
    url = "http://example.com/path/page.html?query=1"
    normalized = normalize_url(url)
    assert normalized == "http://example.com/path/page.html"


def extract_links(soup, base):
    links = []
    for a in soup.find_all('a', href=True):
        url = a['href']
        full_url = urljoin(base, url)
        if is_under_base(full_url, base):
            title = a.text.strip()
            # Use the alt attribute from an <img> tag if available
            img = a.find('img')
            if img and img.has_attr('alt') and img['alt'].strip():
                title = img['alt'].strip()
            links.append((full_url, title))
    return links


def test_extract_links_img_alt():
    base = "http://example.com/"
    html = '''<html><body>
        <a href="page1.html"><img src="img.jpg" alt="Image ALT Text"></a>
    </body></html>'''
    soup = BeautifulSoup(html, 'html.parser')
    links = extract_links(soup, base)
    assert len(links) == 1
    url, title = links[0]
    assert url == "http://example.com/page1.html"
    assert title == "Image ALT Text"
    return links


