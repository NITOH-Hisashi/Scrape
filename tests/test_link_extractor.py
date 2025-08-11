from bs4 import BeautifulSoup
from link_extractor import extract_links, is_under_base, normalize_url


def test_extract_links():
    html = "<a href='https://example.com'>Link</a>"
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://example.com"
    links = extract_links(soup, base_url)
    assert links == [("https://example.com", "Link")]


def test_extract_links_with_img_alt():
    html = "<img src='img.jpg' alt='Image Alt'>"
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://example.com"
    links = extract_links(soup, base_url)
    assert links == [("https://example.com/img.jpg", "Image Alt")]


def test_is_under_base():
    assert is_under_base("https://example.com/page", "https://example.com")


def test_normalize_url():
    url = "https://example.com/page?x=1#top"
    assert normalize_url(url) == "https://example.com/page"
