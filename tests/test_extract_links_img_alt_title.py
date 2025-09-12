# tests/test_extract_links_img_alt_title.py
from bs4 import BeautifulSoup
from link_extractor import extract_links


def test_extract_links_with_img_alt_and_title():
    base_url = "http://example.com"
    html = """
    <html>
      <body>
        <a href="/page1">
          LinkText
          <img src="image.jpg" alt="AltText" title="TitleText">
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
    # alt属性とtitle属性の両方がテキストに追加されている
    assert "LinkText" in text
    assert "AltText" in text
    assert "TitleText" in text
    # alt属性が先に追加されている
    assert text.index("AltText") < text.index("TitleText")
    # 余分な空白が入っていない
    assert text.strip() == "LinkText AltText TitleText" 
    assert "  " not in text
    assert "\n" not in text
    assert "\t" not in text 
    assert "\r" not in text
    assert "\x0b" not in text
    assert "\x0c" not in text
    assert "\xa0" not in text
    assert "\u3000" not in text
    assert "\u200b" not in text
    assert "\ufeff" not in text
    assert "\u200e" not in text
    assert "\u200f" not in text
    assert "\u2028" not in text
    assert "\u2029" not in text
    assert "\u00a0" not in text
    assert "\u2000" not in text
    assert "\u2001" not in text
    assert "\u2002" not in text
    assert "\u2003" not in text
    assert "\u2004" not in text
    assert "\u2005" not in text
    assert "\u2006" not in text
    assert "\u2007" not in text
    assert "\u2008" not in text
    assert "\u2009" not in text
    assert "\u200a" not in text
    assert "\u202f" not in text
    assert "\u205f" not in text
    assert "\u3000" not in text 
    assert "\u180e" not in text
    assert "\u200b" not in text
    assert "\u200c" not in text
    assert "\u200d" not in text
    assert "\u2060" not in text
    assert "\u2061" not in text
    assert "\u2062" not in text
    assert "\u2063" not in text
    assert "\u2064" not in text
    assert "\u2065" not in text
    assert "\u2066" not in text
    assert "\u2067" not in text
    assert "\u2068" not in text
    assert "\u2069" not in text
    