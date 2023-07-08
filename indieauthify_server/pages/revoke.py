"""
IndieAuthify: pages package; revoke token page module
"""

from http import HTTPStatus
import sqlite3

from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from indieauthify_server.dependencies.settings import get_settings
from indieauthify_server.dependencies.flash import flash_message


async def render_revoke_page(request: Request, token: str) -> Response:
    """
    Render the revoke token page
    """

    if not token:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={'error': 'invalid_request'}
        )

    try:
        settings = get_settings()
        connection = sqlite3.connect(settings.token_db_path)

        with connection:
            cursor = connection.cursor()
            if token == 'all':
                cursor.execute("DELETE FROM issued_tokens")
            else:
                cursor.execute("DELETE FROM issued_tokens WHERE token = ?", (token,))

            flash_message(request, 'Your token was revoked', 'success')

    except sqlite3.Error as exc:
        flash_message(request, f'There was an error revoking your token: {exc}', 'error')

    return RedirectResponse(url=str(request.url_for('issued_page')))
