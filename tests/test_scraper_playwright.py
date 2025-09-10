import pytest
from scraper import scrape_page
from models import ScrapedPage


@pytest.fixture
def mock_playwright(monkeypatch):
    """Playwrightのブラウザ操作をモック化"""

    class MockPage:
        def goto(self, url, wait_until=None):
            pass

        def content(self):
            return (
                "<html><head><title>Mock Title</title></head>"
                "<body>Mock Content</body></html>"
            )

        def title(self):
            return "Mock Title"

        def set_extra_http_headers(self, headers):
            pass

    class MockBrowser:
        def new_page(self):
            return MockPage()

        def close(self):
            pass

    class MockPlaywright:
        chromium = type(
            "chromium", (), {"launch": lambda self, headless: MockBrowser()}
        )()

    def mock_sync_playwright():
        class Context:
            def __enter__(self):
                return MockPlaywright()

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return Context()

    monkeypatch.setattr("scraper.sync_playwright", mock_sync_playwright)


def test_scrape_page_with_playwright(monkeypatch, mock_playwright):
    monkeypatch.setattr("config.USE_PLAYWRIGHT_PATTERNS", ["mocksite.com"])
    page = scrape_page("https://mocksite.com/page")
    assert isinstance(page, ScrapedPage)
    assert page.title == "Mock Title"
    assert "Mock Content" in page.content
    assert page.status_code == 200
    assert page.error_message is None
