from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import datetime
import mysql.connector
from config import DB_CONFIG


def fetch_and_store_robots(domain, user_agent="MyScraperBot"):
    """robots.txtを取得してDBに保存"""
    robots_url = f"https://{domain}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        rp.read()
        disallow = "\n".join(rp.disallow_all if hasattr(rp, "disallow_all") else [])
        allow = "\n".join(rp.allow_all if hasattr(rp, "allow_all") else [])
        delay = rp.crawl_delay(user_agent)

        now = datetime.datetime.now(datetime.UTC)
        expires = now + datetime.timedelta(hours=24)

        sql = """
            INSERT INTO robots_rules 
            (domain, user_agent, disallow, allow, crawl_delay, fetched_at, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            disallow = VALUES(disallow),
            allow = VALUES(allow),
            crawl_delay = VALUES(crawl_delay),
            fetched_at = VALUES(fetched_at),
            expires_at = VALUES(expires_at)
        """

        cursor.execute(sql, (domain, user_agent, disallow, allow, delay, now, expires))
        conn.commit()

    finally:
        cursor.close()
        conn.close()


def check_robots_rules(url, user_agent="MyScraperBot"):
    """robots.txtのルールをチェック"""
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
        if rules["disallow"]:
            for pattern in rules["disallow"].split("\n"):
                if pattern and path.startswith(pattern):
                    return False, 0

        # Allowルールをチェック
        if rules["allow"]:
            for pattern in rules["allow"].split("\n"):
                if pattern and path.startswith(pattern):
                    return True, rules["crawl_delay"] or 0

        return True, rules["crawl_delay"] or 0

    finally:
        cursor.close()
        conn.close()
