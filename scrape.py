import requests
from bs4 import BeautifulSoup
import mysql.connector
from datetime import datetime
import hashlib

def get_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def scrape(url):
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else ''
        content = soup.get_text()
        hash_value = get_hash(content)
        return {
            'url': url,
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
            'fetched_at': datetime.now(),
            'title': None,
            'content': None,
            'status_code': None,
            'hash': None,
            'error_message': str(e)
        }

def save_to_mysql(data):
    conn = mysql.connector.connect(
        host='localhost',
        user='your_user',
        password='your_password',
        database='your_database'
    )
    cursor = conn.cursor()
    sql = '''
        INSERT INTO scraped_pages (url, fetched_at, title, content, status_code, hash, error_message)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    '''
    cursor.execute(sql, (
        data['url'], data['fetched_at'], data['title'],
        data['content'], data['status_code'],
        data['hash'], data['error_message']
    ))
    conn.commit()
    cursor.close()
    conn.close()

# 実行例
urls = ['https://example.com', 'https://example.org']
for url in urls:
    result = scrape(url)
    save_to_mysql(result)
