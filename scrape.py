import requests
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime
import hashlib

# ハッシュ値を生成する関数
def get_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

# スクレイピングを行う関数
def scrape(url, referrer=None):
    try:
        headers = {'Referer': referrer} if referrer else {}
        response = requests.get(url, headers=headers, timeout=10)
        status_code = response.status_code
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else ''
        content = soup.get_text()
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
    except Exception as e:
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

# MySQLに保存する関数
def save_to_mysql(data):
    conn = mysql.connector.connect(
        host='localhost',
        user='your_user',
        password='your_password',
        database='your_database'
    )
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

# 実行例
urls = ['https://example.com', 'https://example.org']
for url in urls:
    result = scrape(url)
    save_to_mysql(result)

#   Check if a URL is under a base URL
def is_under_base(url, base_url):
    return url.startswith(base_url)

#   Extract links from a BeautifulSoup object
def extract_links(soup, base_url):
    links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        full_url = requests.compat.urljoin(base_url, href)
        if is_under_base(full_url, base_url):
            title = a.get_text(strip=True)
            # 画像がアンカー内にある場合
            img = a.find('img')
            if img:
                alt = img.get('alt') or img.get('title') or ''
                title = title or alt
            links.append((full_url, title))
    return links

#   Crawl and store pages in the database
def crawl_and_store(base_url):
    while True:
        conn = mysql.connector.connect(...)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM scraped_pages WHERE processed = FALSE")
        rows = cursor.fetchall()
        if not rows:
            break

        for row in rows:
            url = row['url']
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                content = soup.get_text()
                title = soup.title.string if soup.title else ''
                hash_value = get_hash(content)
                fetched_at = datetime.now()

                # 更新：表示内容保存
                cursor.execute("""
                    UPDATE scraped_pages SET
                        content = %s, title = %s, fetched_at = %s,
                        status_code = %s, hash = %s, processed = TRUE
                    WHERE id = %s
                """, (content, title, fetched_at, response.status_code, hash_value, row['id']))

                # リンク抽出と追加
                links = extract_links(soup, base_url)
                for link_url, link_title in links:
                    cursor.execute("SELECT COUNT(*) FROM scraped_pages WHERE url = %s", (link_url,))
                    if cursor.fetchone()['COUNT(*)'] == 0:
                        cursor.execute("""
                            INSERT INTO scraped_pages (url, referrer, title)
                            VALUES (%s, %s, %s)
                        """, (link_url, url, link_title))

                conn.commit()
            except Exception as e:
                cursor.execute("""
                    UPDATE scraped_pages SET error_message = %s, processed = TRUE
                    WHERE id = %s
                """, (str(e), row['id']))
                conn.commit()

        cursor.close()
        conn.close()

from urllib.robotparser import RobotFileParser

#   Check if a URL is allowed by robots.txt
def is_allowed_by_robots(url, user_agent='MyScraperBot'):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    rp = RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        return rp.can_fetch(user_agent, url)
    except:
        return False  # 読み込み失敗時は安全のため拒否

import requests
from datetime import datetime

#   Fetch a URL with If-Modified-Since header
def fetch_if_modified(url, last_fetched_at):
    headers = {}
    if last_fetched_at:
        headers['If-Modified-Since'] = last_fetched_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
    response = requests.get(url, headers=headers, timeout=10)
    return response

#   Mark a row as processed in the database
def mark_as_processed(row_id, note=None):
    conn = mysql.connector.connect(
        host='localhost
for row in unprocessed_rows:
    url = row['url']
    last_fetched = row['fetched_at']

    # robots.txt チェック
    if not is_allowed_by_robots(url):
        mark_as_error(row['id'], "Blocked by robots.txt")
        continue

    # 更新チェック付き取得
    try:
        response = fetch_if_modified(url, last_fetched)
        if response.status_code == 304:
            mark_as_processed(row['id'], note="Not modified")
            continue

        # 通常処理（保存・リンク抽出など）
        process_page(response, row)

    except Exception as e:
        mark_as_error(row['id'], str(e))

