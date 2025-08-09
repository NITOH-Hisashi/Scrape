import unittest
from bs4 import BeautifulSoup
from link_extractor import extract_links, is_under_base, normalize_url

class TestLinkExtractor(unittest.TestCase):
    def test_extract_links(self):
        html = '''
        <html><body>
        <a href="/page1">Page 1</a>
        <a href="https://example.com/page2">Page 2</a>
        </body></html>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        base_url = "https://example.com/"
        links = extract_links(soup, base_url)
        self.assertIn(("https://example.com/page1", "Page 1"), links)
        self.assertIn(("https://example.com/page2", "Page 2"), links)

    def test_extract_links_with_img_alt(self):
        html = '<a href="/img"><img src="x.jpg" alt="Image Link"></a>'
        soup = BeautifulSoup(html, 'html.parser')
        links = extract_links(soup, "https://example.com")
        assert ("https://example.com/img", "Image Link") in links

    def test_is_under_base(self):
        assert is_under_base("https://example.com/page", "https://example.com")
        assert not is_under_base("https://other.com/page", "https://example.com")

    def test_normalize_url(self):
        url = "https://example.com/page?x=1#top"
        assert normalize_url(url) == "https://example.com/page"

if __name__ == '__main__':
    unittest.main()
