import unittest
from bs4 import BeautifulSoup
from link_extractor import extract_links

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

if __name__ == '__main__':
    unittest.main()
