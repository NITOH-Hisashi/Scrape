from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime, timedelta
from datetime import datetime
from urllib.parse import urljoin
import hashlib
from config import DB_CONFIG
from link_extractor import extract_links
    return links
def scrape(url, referrer=None):
    try:
        headers = {'Referer': referrer} if referrer else {}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # HTTPエラーをチェック

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string if soup.title else None
        content = soup.get_text(strip=True)
        status_code = response.status_code
        hash_value = get_hash(content)

        return {
            'url': url,
            'referrer': referrer,
            'fetched_at': datetime.now(),
            'title': title,
            'content': content,
            'status_code': status_code,
            'hash': hash_value,
            'error_message': None
        }
    except requests.RequestException as e:
        return {
            'url': url,
            'referrer': referrer,
            'fetched_at': datetime.now(),
            'title': None,
            'content': None,
            'status_code': None,
            'hash': None,
            'error_message': str(e)
        }   

def is_under_base(url, base_url):
    parsed_url = urlparse(url)
    parsed_base = urlparse(base_url)
    return parsed_url.netloc == parsed_base.netloc and parsed_url.path.startswith(parsed_base.path)
def get_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
def save_to_mysql(data):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    sql = '''
        INSERT INTO scraped_pages (url, referrer, fetched_at, title, content, status_code, hash, error_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    '''
    cursor.execute(sql, (
        data['url'], data['referrer'], data['fetched_at'], data['title'],
        data['content'], data['status_code'], data['hash'], data['error_message']
    ))
    conn.commit()
    cursor.close()
    conn.close()    

# robots.txtを取得してDBに保存する関数    
def fetch_and_store_robots(domain, user_agent='MyScraperBot'):
    robots_url = f"https://{domain}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        disallow = '\n'.join(rp.disallow_all if rp.disallow_all else [])
        allow = '\n'.join(rp.allow_all if rp.allow_all else [])
        delay = rp.crawl_delay(user_agent)

        now = datetime.utcnow()
        expires = now + timedelta(hours=24)

        # DB保存（UPSERT）
        conn = mysql.connector.connect(
            host='localhost',
            user='your_user',
            password='your_password',
            database='your_database'
        )
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO robots_rules (domain, user_agent, disallow, allow, crawl_delay, fetched_at, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                disallow = VALUES(disallow),
                allow = VALUES(allow),
                crawl_delay = VALUES(crawl_delay),
                fetched_at = VALUES(fetched_at),
                expires_at = VALUES(expires_at)
        """, (domain, user_agent, disallow, allow, delay, now, expires))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"robots.txt fetch failed for {domain}: {e}")

# robots.txtのルールに基づいてURLが取得可能か確認する関数
def can_fetch_from_db(path, rules_row):
    disallowed = rules_row['disallow'].split('\n') if rules_row['disallow'] else []
    allowed = rules_row['allow'].split('\n') if rules_row['allow'] else []

    for allow_rule in allowed:
        if path.startswith(allow_rule):
            return True
    for disallow_rule in disallowed:
        if path.startswith(disallow_rule):
            return False
    return True  # 明示されていない場合は許可

