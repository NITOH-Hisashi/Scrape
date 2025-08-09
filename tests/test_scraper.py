import unittest
from scraper import get_hash, scrape

class TestScraper(unittest.TestCase):
    def test_get_hash(self):
        text = "hello"
        expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        self.assertEqual(get_hash(text), expected_hash)

    def test_scrape_valid_url(self):
        url = "https://example.com"
        page = scrape(url)
        self.assertEqual(page.url, url)
        self.assertIsNotNone(page.content)
        self.assertIsNone(page.error_message)

    def test_scrape_invalid_url(self):
        url = "https://invalid.url"
        page = scrape(url)
        self.assertEqual(page.url, url)
        self.assertIsNotNone(page.error_message)

if __name__ == '__main__':
    unittest.main()
