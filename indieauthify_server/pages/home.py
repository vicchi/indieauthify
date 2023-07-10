"""
IndieAuthify: pages package; home page module
"""

from fastapi.requests import Request
from fastapi.responses import Response

from indieauthify_server.dependencies.templates import get_template_engine


async def render_home_page(request: Request) -> Response:
    """
    Render the landing/home page
    """

    args = {
        'request': request
    }

    return get_template_engine().TemplateResponse('index.html.j2', args)
