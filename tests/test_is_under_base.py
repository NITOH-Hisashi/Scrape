# tests/test_is_under_base.py
import pytest
from link_extractor import is_under_base


@pytest.mark.parametrize(
    "url, base_url, expected",
    [
        # 同一ドメイン & base_url配下 → True
        ("http://example.com/path/page", "http://example.com/path", True),
        ("http://example.com/path/sub/page", "http://example.com/path", True),
        # 同一ドメインだがパスが配下でない → False
        ("http://example.com/other/page", "http://example.com/path", False),
        # ドメインが異なる → False
        ("http://other.com/path/page", "http://example.com/path", False),
        # base_urlのパスがルートの場合 → 同一ドメインならTrue
        ("http://example.com/anything", "http://example.com/", True),
        # base_urlのパスが空文字の場合 → 同一ドメインならTrue
        ("http://example.com/anything", "http://example.com", True),
        # サブドメインは別ドメイン扱い → False
        ("http://sub.example.com/path", "http://example.com/path", False),
    ],
)
def test_is_under_base(url, base_url, expected):
    assert is_under_base(url, base_url) is expected


def test_is_under_base_invalid_url():
    """無効なURLの場合はFalseを返す"""
    assert is_under_base("not a url", "http://example.com") is False
    assert is_under_base("http://example.com", "not a url") is False
    assert is_under_base("not a url", "also not a url") is False
