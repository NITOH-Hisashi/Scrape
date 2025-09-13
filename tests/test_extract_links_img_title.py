# tests/test_extract_links_img_title.py
from bs4 import BeautifulSoup
from link_extractor import extract_links


def test_extract_links_with_img_title():
    base_url = "http://example.com"
    html = """
    <html>
      <body>
        <a href="/page1">
          LinkText
          <img src="image.jpg" title="ImageTitle">
        </a>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    links = extract_links(soup, base_url)

    # 1件だけ抽出されるはず
    assert len(links) == 1
    url, text = links[0]

    # URLは正規化されている
    assert url == "http://example.com/page1"
    # title属性の文字列がテキストに追加されている
    assert "LinkText" in text
    assert "ImageTitle" in text
    # imgタグのtitle属性がテキストに追加されている
    assert text.strip() == "LinkText ImageTitle"
    # 余分な空白が入っていない
    assert "  " not in text
    assert "\n" not in text
    assert "\t" not in text
    assert "\r" not in text
