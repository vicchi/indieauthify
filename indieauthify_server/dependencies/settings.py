"""
IndieAuthify: dependencies package; settings module
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

import dotenv

from pydantic import BaseSettings, HttpUrl


class Settings(BaseSettings):
    """
    IndieAuthify server settings
    """

    app_env: str

    me: HttpUrl

    github_client_secret: str
    github_client_id: str
    github_base_url: HttpUrl
    github_token_url: HttpUrl
    github_authorize_url: HttpUrl

    session_key: str
    api_key: str

    webhook_server: Optional[bool] = False
    webhook_url: Optional[str] = None
    webhook_api_key: Optional[str] = None

    rpc_timeout: int

    token_db_path: Path

    class Config:    # pylint: disable=too-few-public-methods
        """
        IndieAuthify server settings config
        """

        env_file = dotenv.find_dotenv()


@lru_cache
def get_settings():
    """
    Find and return the settings in the current .env
    """

    return Settings()
