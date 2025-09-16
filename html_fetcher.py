from playwright.sync_api import sync_playwright
import requests


def fetch_html(
    url: str,
    use_playwright: bool = False,
    method: str = "GET",
    payload: dict | None = None,
    headers: dict | None = None,
    emulate_form: bool = False,
) -> str:
    """
    HTML取得関数：GET/POSTとPlaywright/requestsを切り替え可能
    - method: "GET" or "POST"
    - payload: POST時のフォームデータ
    - headers: 任意のHTTPヘッダー
    - use_playwright: TrueならPlaywrightで取得
    - emulate_form: TrueならPlaywrightでフォーム送信をエミュレート
    """
    headers = headers or {}

    if use_playwright:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            if method.upper() == "POST":
                if emulate_form:
                    # フォーム送信をエミュレート
                    page.goto("about:blank")
                    form_html = f"<form id='f' method='POST' action='{url}'></form>"
                    page.set_content(form_html)
                    for k, v in (payload or {}).items():
                        page.evaluate(
                            f"""
                            var input = document.createElement('input');
                            input.name = '{k}';
                            input.value = '{v}';
                            document.getElementById('f').appendChild(input);
                        """
                        )
                    page.evaluate("document.getElementById('f').submit()")
                    page.wait_for_load_state("networkidle")
                    content = page.content()
                else:
                    # Playwrightのrequest APIを使用（画面取得ではない）
                    request_context = p.request.new_context()
                    response = request_context.post(url, data=payload, headers=headers)
                    content = response.text()
            else:
                page.goto(url)
                page.wait_for_load_state("networkidle")
                content = page.content()

            browser.close()
            return content

    else:
        if method.upper() == "POST":
            response = requests.post(url, data=payload, headers=headers)
        else:
            response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
