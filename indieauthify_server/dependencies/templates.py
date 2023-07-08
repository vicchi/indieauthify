"""
IndieAuthify: dependencies package; Jinja template factory module
"""

from functools import lru_cache
from pathlib import Path

from fastapi.templating import Jinja2Templates

from indieauthify_server.dependencies.flash import get_flash_messages, has_flash_messages


def get_template_dir() -> str:
    """
    Returns the templates directory
    """

    app_root = Path(__file__).parents[2]
    return str(app_root / 'templates')


@lru_cache
def get_template_engine() -> Jinja2Templates:
    """
    Get a template engine instance
    """

    engine = Jinja2Templates(directory=get_template_dir())

    engine.env.trim_blocks = True
    engine.env.lstrip_blocks = True

    engine.env.globals['get_flash_messages'] = get_flash_messages
    engine.env.globals['has_flash_messages'] = has_flash_messages

    return engine
