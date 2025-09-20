from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl
from functools import lru_cache
from typing import List
import os


USE_PLAYWRIGHT_PATTERNS = ["example.com", "/dynamic/"]


class Settings(BaseSettings):
    # v2 スタイル: SettingsConfigDict を利用
    # SettingsConfigDict は TypedDict なので辞書リテラルで代入
    model_config: SettingsConfigDict = {
        "env_file": f".env.{os.getenv('ENV', 'local')}",
        "env_file_encoding": "utf-8",
    }

    # 環境識別 (local / test / prod)
    env: str = "local"

    # DB 接続文字列 (MySQL / SQLite 両対応)
    database_url: AnyUrl = AnyUrl(
        "mysql://your_user:your_password@localhost:3306/scraping_db"
    )

    db_pool_size: int = 5
    debug: bool = False

    # Playwright を使う対象パターン
    use_playwright_patterns: List[str] = USE_PLAYWRIGHT_PATTERNS


@lru_cache
def get_settings() -> Settings:
    """Settings をキャッシュして何度も生成しない"""
    return Settings()


# アプリ全体で import して使うインスタンス
settings = get_settings()
