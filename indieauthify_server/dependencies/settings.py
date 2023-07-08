"""
IndieAuthify: dependencies package; settings module
"""

from functools import lru_cache
from pathlib import Path

import dotenv

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    IndieAuthify server settings
    """

    app_env: str

    me: str

    github_client_id: str
    github_oauth_redirect: str
    github_client_secret: str

    session_key: str
    api_key: str

    webhook_server: bool = False
    webhook_url: str = None
    webhook_api_key: str = None

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
