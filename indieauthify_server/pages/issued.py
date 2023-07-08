"""
IndieAuthify: pages package; issued tokens page module
"""

from http import HTTPStatus
import json
import sqlite3

from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response
import indieweb_utils

from indieauthify_server.dependencies.settings import get_settings
from indieauthify_server.dependencies.templates import get_template_engine


async def render_issued_page(
    request: Request,
    feed: str = 'false',
    authorization: str | None = None,
    token: str | None = None
) -> Response:
    """
    Render the issues and issue detail page
    """

    settings = get_settings()
    if token:
        connection = sqlite3.connect(settings.token_db_path)

        with connection:
            cursor = connection.cursor()

            issued_tokens = cursor.execute('SELECT * FROM issued_tokens WHERE token = ?',
                                           (token,
                                           )).fetchone()

            if len(issued_tokens) == 0:
                raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='No tokens found')

        token_app = json.loads(issued_tokens[5])

        args = {
            'request': request,
            'title': 'About an Issued Token',
            'token_app': token_app,
            'token': issued_tokens,
            'SCOPE_DEFINITIONS': indieweb_utils.SCOPE_DEFINITIONS
        }
        return get_template_engine().TemplateResponse('single_token.html.j2', args)

    if not request.session.get("logged_in") and authorization != settings.api_key:
        return RedirectResponse(url=request.url_for('get_login_page'))

    connection = sqlite3.connect(settings.token_db_path)

    with connection:
        cursor = connection.cursor()

        issued_tokens = cursor.execute('SELECT * FROM issued_tokens').fetchall()

    if feed == 'true':
        template = 'issued_feed.html.j2'
    else:
        template = 'issued.html.j2'

    args = {
        'request': request,
        'title': 'Issued Token',
        'issued_tokens': issued_tokens,
        'SCOPE_DEFINITIONS': indieweb_utils.SCOPE_DEFINITIONS
    }
    return get_template_engine().TemplateResponse(name=template, context=args)
