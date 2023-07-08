"""
IndieAuthify: pages package; home page module
"""

from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response


async def render_logout_page(request: Request) -> Response:
    """
    Render the logout page, which isn't really a page
    """

    response = RedirectResponse(url='/')
    request.session.pop('logged_in', None)
    request.session.clear()

    return response
