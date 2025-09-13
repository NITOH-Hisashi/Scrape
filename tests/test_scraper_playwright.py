import pytest
import types
import config
from scraper import scrape_page, ScrapedPage


class DummyPage:
    def __init__(self, title="Mock Title", content="<html></html>"):
        self._title = title
        self._content = content

    def set_extra_http_headers(self, headers):
        pass

    def goto(self, url, wait_until=None):
        pass

    def title(self):
        return self._title

    def content(self):
        return self._content


class DummyBrowser:
    def new_page(self):
        return DummyPage()

    def close(self):
        pass


class DummyPlaywright:
    def __enter__(self):
        return types.SimpleNamespace(
            chromium=types.SimpleNamespace(launch=lambda headless=True: DummyBrowser())
        )

    def __exit__(self, exc_type, exc, tb):
        pass


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


def test_scrape_page_with_playwright(monkeypatch):
    monkeypatch.setattr(config, "USE_PLAYWRIGHT_PATTERNS", ["amus.biz"])
    monkeypatch.setattr("scraper.sync_playwright", lambda: DummyPlaywright())

    page = scrape_page("https://amus.biz")
    assert isinstance(page, ScrapedPage)
    # 実装の仕様に合わせて期待値を決める
    # 1) title() を優先
    # 2) title() が空なら URL のホスト名
    # 3) それも空なら None
    # 実在のページを使う場合は、タイトルが変わる可能性があるので注意
    assert page.title == "AMUSEMENT PROJECT Groups AMU'S"
    assert page.error_message is None
    assert (
        page.content is not None
        and "<title>AMUSEMENT PROJECT Groups AMU'S</title>" in page.content
    )
    assert page.url == "https://amus.biz"
    assert page.status_code == 200
    assert page.hash is not None
    assert page.hash != ""  # 空文字列ではないことを確認
