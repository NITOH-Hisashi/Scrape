import requests
from bs4 import BeautifulSoup
import mysql.connector
import hashlib
from urllib.parse import urlparse
from fetch_and_store_robots import fetch_and_store_robots
from models import ScrapedPage


# ハッシュ値を生成する関数
def get_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# スクレイピングを行う関数
def scrape(url, referrer=None):
    try:
        headers = {"Referer": referrer} if referrer else {}
        response = requests.get(url, headers=headers, timeout=10)
        status_code = response.status_code
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string if soup.title else ""
        content = response.text  # HTML全体を保存
        hash_value = get_hash(content)
        return ScrapedPage(
            url=url,
            title=title,
            content=content,
            status_code=status_code,
            hash_value=hash_value,
            error_message=None,
        )
    except Exception as e:
        return ScrapedPage(
            url=url,
            title=None,
            content=None,
            status_code=None,
            hash_value=None,
            error_message=str(e),
        )


# MySQLにスクレイピング結果を保存する関数
def save_to_mysql(data):
    from config import DB_CONFIG

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        sql = """
            INSERT INTO scraped_pages (
                url,
                referrer,
                fetched_at,
                title,
                content,
                status_code,
                hash,
                error_message,
                processed
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)
            ON DUPLICATE KEY UPDATE
            referrer = VALUES(referrer),
            fetched_at = VALUES(fetched_at),
            title = VALUES(title),
            content = VALUES(content),
            status_code = VALUES(status_code),
            hash = VALUES(hash),
            error_message = VALUES(error_message),
            processed = FALSE
        """
        cursor.execute(
            sql,
            (
                data["url"],
                data["referrer"],
                data["fetched_at"],
                data["title"],
                data["content"],
                data["status_code"],
                data["hash"],
                data["error_message"],
            ),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


# URLがベースURL配下かどうかをチェック
def is_under_base(url, base_url):
    return url.startswith(base_url)


# robots.txtのルールをチェックする関数
def check_robots_rules(url, user_agent="MyScraperBot"):
    from config import DB_CONFIG

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)

    try:
        domain = urlparse(url).netloc

        # robots_rulesテーブルをチェック
        cursor.execute(
            """
            SELECT * FROM robots_rules
            WHERE domain = %s AND user_agent = %s
            AND expires_at > NOW()
        """,
            (domain, user_agent),
        )

        rules = cursor.fetchone()

        # ルールが存在しないか期限切れの場合は更新
        if not rules:
            fetch_and_store_robots(domain, user_agent)
            cursor.execute(
                """
                SELECT * FROM robots_rules
                WHERE domain = %s AND user_agent = %s
            """,
                (domain, user_agent),
            )
            rules = cursor.fetchone()

        if not rules:
            return True, 0  # ルールが取得できない場合はデフォルトで許可

        # パスに対するアクセス可否を判定
        path = urlparse(url).path or "/"

        # Disallowルールをチェック
        if (
            rules
            and isinstance(rules, dict)
            and "disallow" in rules
            and rules["disallow"]
        ):
            for pattern in rules["disallow"].split("\n"):  # type: ignore
                if pattern and path.startswith(str(pattern)):
                    return False, 0

        # Allowルールをチェック
        if rules and isinstance(rules, dict) and "allow" in rules and rules["allow"]:
            for pattern in rules["allow"].split("\n"):  # type: ignore
                if pattern and path.startswith(str(pattern)):
                    return True, (
                        rules["crawl_delay"] if rules["crawl_delay"] is not None else 0
                    )

        return True, rules["crawl_delay"] if rules["crawl_delay"] is not None else 0  # type: ignore

    finally:
        cursor.close()
        conn.close()


# BeautifulSoupオブジェクトからリンクを抽出
def extract_links(soup, base_url):
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        from urllib.parse import urljoin

        full_url = urljoin(base_url, href)
        if is_under_base(full_url, base_url):
            title = a.get_text(strip=True)
            # 画像がアンカー内にある場合
            img = a.find("img")
            if img:
                alt = img.get("alt") or img.get("title") or ""
                title = title or alt
            links.append((full_url, title))
    return links
