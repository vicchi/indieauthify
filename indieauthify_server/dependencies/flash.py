"""
IndieAuthify: flash messages module
"""

from typing import Dict, List

from fastapi.requests import Request

FLASH_PROPERTY = '_messages'


def flash_message(request: Request, message: str, category: str) -> None:
    """
    Add a flash message to the current session
    """

    if FLASH_PROPERTY not in request.session:
        request.session[FLASH_PROPERTY] = []

    request.session[FLASH_PROPERTY].append({
        'message': message,
        'category': category
    })


def has_flash_messages(request: Request) -> bool:
    """
    Does the current session have any flash messages?
    """

    if FLASH_PROPERTY in request.session and request.session[FLASH_PROPERTY]:
        return True

    return False


def get_flash_messages(request: Request) -> List[Dict]:
    """
    Get any flash messages associated with the current session
    """

    try:
        flashes = request.state.flashes
    except AttributeError:
        flashes = request.session.pop(FLASH_PROPERTY) if FLASH_PROPERTY in request.session else []
        request.state.flashes = flashes

    return flashes
