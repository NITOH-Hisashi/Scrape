import unittest
from link_extractor import extract_links, is_under_base, normalize_url

class TestLinkExtractor(unittest.TestCase):
    def test_extract_links(self):
        html = "<a href='https://example.com'>Link</a>"
        links = extract_links(html)
        assert links == [("https://example.com", "Link")]

    def test_extract_links_with_img_alt(self):
        html = "<img src='img.jpg' alt='Image Alt'>"
        links = extract_links(html)
        assert links == [("img.jpg", "Image Alt")]

    def test_is_under_base(self):
        assert is_under_base("https://example.com/page", "https://example.com")

    def test_normalize_url(self):
        url = "https://example.com/page?x=1#top"
        assert normalize_url(url) == "https://example.com/page"
