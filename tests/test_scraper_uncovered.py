# tests/test_scraper_uncovered.py
import types
import scraper
import config
import models


class DummyPage:
    def __init__(self, content="<html><title>T</title></html>", title="T"):
        self._content = content
        self._title = title

    def content(self):
        return self._content

    def title(self):
        return self._title

    def set_extra_http_headers(self, headers):
        pass

    def goto(self, url, wait_until=None):
        pass


class DummyBrowser:
    def new_page(self):
        return DummyPage()

    def close(self):
        pass


class DummyPlaywright:
    def __enter__(self):
        return types.SimpleNamespace(
            chromium=types.SimpleNamespace(launch=lambda headless: DummyBrowser())
        )

    def __exit__(self, exc_type, exc, tb):
        pass


def test_should_scrape_blocked(monkeypatch):
    monkeypatch.setattr(scraper, "check_robots_rules", lambda u, ua: (False, 0))
    called = {}
    monkeypatch.setattr(
        scraper,
        "mark_page_as_processed",
        lambda u, m=None: called.setdefault("marked", True),
    )
    assert scraper.should_scrape("http://x", "UA") is False
    assert called["marked"]


def test_should_scrape_with_delay(monkeypatch):
    monkeypatch.setattr(scraper, "check_robots_rules", lambda u, ua: (True, 0.1))
    monkeypatch.setattr(
        scraper.time, "sleep", lambda s: called.setdefault("slept", True)
    )
    called = {}
    assert scraper.should_scrape("http://x", "UA") is True


def test_scrape_page_playwright(monkeypatch):
    monkeypatch.setattr(scraper, "sync_playwright", lambda: DummyPlaywright())
    monkeypatch.setattr(scraper, "get_hash", lambda t: "hash")
    page = scraper.scrape_page("http://example.com/playwright")
    assert page.title == "T"


def test_scrape_page_exception(monkeypatch):
    # Playwright分岐を回避（空リストにする）
    monkeypatch.setattr(config, "USE_PLAYWRIGHT_PATTERNS", [])

    # requests.get を例外発生にモック
    def raise_exc(*a, **k):
        raise Exception("fail")

    monkeypatch.setattr(scraper.requests, "get", raise_exc)

    page = scraper.scrape_page("http://example.com")
    assert page.error_message is not None
    assert "fail" in page.error_message


def test_fetch_post_content_exception(monkeypatch):
    monkeypatch.setattr(
        scraper.requests,
        "post",
        lambda *a, **k: (_ for _ in ()).throw(Exception("postfail")),
    )
    page = scraper.fetch_post_content("http://x", data={})
    assert page.error_message is not None and "postfail" in page.error_message


def test_extract_and_save_links_existing(monkeypatch):
    page = types.SimpleNamespace(content="<html></html>", url="http://base")
    monkeypatch.setattr(
        scraper, "extract_links", lambda s, u: [("http://link", "title")]
    )
    monkeypatch.setattr(scraper, "exists_in_db", lambda u: True)  # 既存URL
    called = {}
    monkeypatch.setattr(
        scraper, "save_page_to_db", lambda p: called.setdefault("saved", True)
    )
    scraper.extract_and_save_links(page)
    assert "saved" not in called  # 保存されない


def test_process_single_page_blocked(monkeypatch):
    row = {"url": "http://x"}
    monkeypatch.setattr(scraper, "should_scrape", lambda u, ua: False)
    scraper.process_single_page(row, "UA")  # return して何もせず


def test_process_single_page_empty_content(monkeypatch):
    row = {"url": "http://x"}
    page = types.SimpleNamespace(content="", error_message=None)
    monkeypatch.setattr(scraper, "should_scrape", lambda u, ua: True)
    monkeypatch.setattr(scraper, "scrape_page", lambda u, r=None: page)
    monkeypatch.setattr(scraper, "save_page_to_db", lambda p: None)
    monkeypatch.setattr(scraper, "mark_page_as_processed", lambda u: None)
    scraper.process_single_page(row, "UA")


def test_process_single_page_error(monkeypatch):
    row = {"url": "http://x"}
    page = types.SimpleNamespace(content="abc", error_message="err")
    monkeypatch.setattr(scraper, "should_scrape", lambda u, ua: True)
    monkeypatch.setattr(scraper, "scrape_page", lambda u, r=None: page)
    monkeypatch.setattr(scraper, "save_page_to_db", lambda p: None)
    monkeypatch.setattr(scraper, "mark_page_as_processed", lambda u: None)
    scraper.process_single_page(row, "UA")


def test_main_with_reset_and_url(monkeypatch):
    args = types.SimpleNamespace(
        user_agent="UA",
        url="http://x",
        referrer=None,
        method="GET",
        payload=None,
        reset=True,
    )
    # argparse のモック
    monkeypatch.setattr(
        scraper.argparse,
        "ArgumentParser",
        lambda **k: types.SimpleNamespace(
            add_argument=lambda *a, **k: None, parse_args=lambda: args
        ),
    )
    # models の reset_all_processed をモック
    monkeypatch.setattr(models, "reset_all_processed", lambda: None)
    # 他の依存関数もモック
    monkeypatch.setattr(scraper, "get_page_counts", lambda: (0, 0))
    monkeypatch.setattr(scraper, "process_single_page", lambda r, user_agent=None: None)
    monkeypatch.setattr(scraper, "process_pages", lambda user_agent=None: None)

    scraper.main()


def test_main_without_url(monkeypatch):
    args = types.SimpleNamespace(
        user_agent="UA",
        url=None,
        referrer=None,
        method="GET",
        payload=None,
        reset=False,
    )
    monkeypatch.setattr(
        scraper.argparse,
        "ArgumentParser",
        lambda **k: types.SimpleNamespace(
            add_argument=lambda *a, **k: None, parse_args=lambda: args
        ),
    )
    monkeypatch.setattr(scraper, "get_page_counts", lambda: (0, 0))
    monkeypatch.setattr(scraper, "process_pages", lambda user_agent=None: None)
    scraper.main()
