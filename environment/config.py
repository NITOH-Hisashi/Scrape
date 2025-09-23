from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl
from functools import lru_cache
from typing import List
import os


class Settings(BaseSettings):
    # 環境識別 (local / test / prod)
    env: str = os.getenv('ENV', 'local')

    # v2 スタイル: SettingsConfigDict を利用
    # SettingsConfigDict は TypedDict なので辞書リテラルで代入
    model_config: SettingsConfigDict = {
        "env_file": f"./environment/.env.{env}",
        "env_file_encoding": "utf-8",
    }
    print(f"[DEBUG] Loading config from {model_config['env_file']}")

    # DB 接続文字列 (MySQL / SQLite 両対応)
    database_url: AnyUrl = AnyUrl(
        "mysql://your_user:your_password@localhost:3306/scraping_db"
    )

    db_pool_size: int = 5
    debug: bool = False

    # Playwright を使う対象パターン
    use_playwright_patterns: List[str] = []


@lru_cache
def get_settings() -> Settings:
    """Settings をキャッシュして何度も生成しない"""
    s = Settings()
    print(f"[DEBUG] Loaded USE_PLAYWRIGHT_PATTERNS: {s.use_playwright_patterns}")
    return s


settings = get_settings()


# アプリ全体で import して使うインスタンス
settings = get_settings()

# 既存の Settings 定義の下に追加
USE_PLAYWRIGHT_PATTERNS = settings.use_playwright_patterns
