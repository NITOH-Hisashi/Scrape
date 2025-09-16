from playwright.sync_api import sync_playwright
import requests


def fetch_html(url: str, use_playwright: bool = False) -> str:
    if use_playwright:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            content = page.content()
            browser.close()
            return content
    else:
        return requests.get(url).text
