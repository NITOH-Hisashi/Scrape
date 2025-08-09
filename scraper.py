import requests
from bs4 import BeautifulSoup
import hashlib
import time

from models import ScrapedPage, save_page_to_db, get_unprocessed_page, mark_page_as_processed
from link_extractor import extract_links
from robots_handler import check_robots_rules

def get_hash(text):
    """ハッシュ値を生成"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def scrape(url, referrer=None):
    """単一ページのスクレイピングを実行"""
    try:
        headers = {'Referer': referrer} if referrer else {}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else ''
        content = response.text  # HTML全体を保存
        hash_value = get_hash(content)
        
        return ScrapedPage(
            url=url,
            referrer=referrer,
            title=title,
            content=content,
            status_code=response.status_code,
            hash_value=hash_value
        )
        
    except Exception as e:
        return ScrapedPage(
            url=url,
            referrer=referrer,
            error_message=str(e)
        )

def process_pages(user_agent='MyScraperBot'):
    """ページの処理を実行"""
    while True:
        # 未処理のページを取得
        row = get_unprocessed_page()
        if not row:
            break
            
        current_url = row['url']
        
        # robots.txtのルールをチェック
        allowed, delay = check_robots_rules(current_url, user_agent)
        
        if not allowed:
            print(f"Skipping {current_url} (blocked by robots.txt)")
            mark_page_as_processed(current_url, "Blocked by robots.txt")
            continue
            
        # クロール遅延を適用
        if delay > 0:
            time.sleep(delay)
        
        # ページをスクレイピング
        page = scrape(current_url, row.get('referrer'))
        save_page_to_db(page)
        
        if page.error_message is None:
            # リンクを抽出して保存
            soup = BeautifulSoup(page.content, 'html.parser')
            links = extract_links(soup, current_url)
            
            for link_url, link_title in links:
                new_page = ScrapedPage(
                    url=link_url,
                    referrer=current_url,
                    title=link_title
                )
                save_page_to_db(new_page)
        
        mark_page_as_processed(current_url)

def main():
    """コマンドライン引数を処理してスクレイピングを実行"""
    import argparse
    parser = argparse.ArgumentParser(description='Web scraping tool with robots.txt compliance')
    parser.add_argument('--user-agent', 
                      default='MyScraperBot',
                      help='User agent string to use for requests (default: MyScraperBot)')
    
    args = parser.parse_args()
    
    print(f"Starting scraper with User-Agent: {args.user_agent}")
    process_pages(user_agent=args.user_agent)

if __name__ == '__main__':
    main()
