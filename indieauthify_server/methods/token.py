"""
IndieAuthify: methods package; token methods handler module
"""

import logging
from dataclasses import asdict
import datetime
from http import HTTPStatus
import json
import secrets
import sqlite3
import time

from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
import indieweb_utils
import jwt
import requests

from indieauthify_server.dependencies.settings import get_settings
from indieauthify_server.dependencies.flash import flash_message
from indieauthify_server.models import TokenParams


async def token_handler(request: Request) -> JSONResponse:    # pylint: disable=too-many-return-statements
    """
    Token handler
    """

    authorization = request.headers.get('authorization')

    if not authorization:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={'error': 'invalid_request'}
        )

    settings = get_settings()
    connection = sqlite3.connect(settings.token_db_path)

    with connection:
        cursor = connection.cursor()

        is_revoked = cursor.execute(
            "SELECT * FROM revoked_tokens WHERE token = ?",
            (authorization,
            )
        ).fetchone()

        if is_revoked:
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={'error': 'invalid_grant'}
            )

    authorization = authorization.replace('Bearer ', '')
    try:
        decoded_authorization_code = jwt.decode(
            authorization,
            settings.session_key,
            algorithms=['HS256']
        )
    except jwt.DecodeError as exc:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                'error': 'invalid_code',
                'details': exc
            }
        )

    if int(time.time()) > decoded_authorization_code['expires']:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={'error': 'invalid_grant'}
        )

    me = decoded_authorization_code['me']    # pylint: disable=invalid-name
    client_id = decoded_authorization_code['client_id']
    scope = decoded_authorization_code['scope']
    resource = decoded_authorization_code['resource']

    if resource != 'all':
        if request['path'] not in resource:
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={'error': 'invalid_request'}
            )

    if 'profile' in scope:
        parsed_profile = indieweb_utils.get_profile(me)

        if parsed_profile:
            content = {
                'me': me.strip('/') + '/',
                'client_id': client_id,
                'scope': scope,
                'profile': asdict(parsed_profile),
            }
            return JSONResponse(status_code=HTTPStatus.OK, content=content)

    content = {
        'me': me.strip('/') + '/',
        'client_id': client_id,
        'scope': scope
    }
    return JSONResponse(status_code=HTTPStatus.OK, content=content)


async def token_form_handler(   # pylint: disable=too-many-arguments
    request: Request,
    params: TokenParams
) -> JSONResponse:
    """
    Token form handler
    """

    settings = get_settings()
    if params.action and params.action == 'revoke':
        connection = sqlite3.connect(settings.token_db_path)

        with connection:
            cursor = connection.cursor()

            cursor.execute("INSERT INTO revoked_tokens VALUES (?)", (params.code,))

        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={}
        )

    if params.grant_type == 'authorization_code':
        access = 'all'
    else:
        db = sqlite3.connect(settings.token_db_path)

        with db:
            cursor = db.cursor()

            ticket = cursor.execute("SELECT * FROM tickets WHERE token = ?",
                                    (params.code,
                                    )).fetchone()

            if not ticket:
                return JSONResponse(
                    status_code=HTTPStatus.BAD_REQUEST,
                    content={'error': 'invalid_ticket'}
                )

            access = ticket[1]

    settings = get_settings()
    try:
        redeem_code = indieweb_utils.redeem_code(
            params.grant_type,
            params.code,
            params.client_id,
            params.redirect_uri,
            params.code_verifier,
            settings.session_key,
            resource=access,
        )

        access_token = redeem_code.access_token
        scope = redeem_code.scope
        me = redeem_code.me    # pylint: disable=invalid-name
    except (
        indieweb_utils.indieauth.server.AuthenticationError,
        indieweb_utils.indieauth.server.AuthorizationCodeExpiredError,
        indieweb_utils.indieauth.server.TokenValidationError
    ) as exc:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                'error': 'invalid_request',
                'details': exc
            }
        )

    content = {
        'access_token': access_token,
        'token_type': 'Bearer',
        'scope': scope,
        'me': me
    }
    return JSONResponse(status_code=HTTPStatus.OK, content=content)


async def generate_token_handler(
    request: Request,
    me: str,
    client_id: str,
    redirect_uri: str,
    response_type: str,
    scope: str,
    is_manually_issued: str,
    state: str | None = None,
    code_challenge_method: str | None = None
) -> Response:
    """
    Generate token handler
    """

    logging.debug('generate_token_handler')
    if not request.session.get("logged_in"):
        return RedirectResponse(url=request.url_for('get_login_page',
                                                    **{'r': str(request.url)}))

    final_scope = ""

    for item in scope.split(" "):
        final_scope.join(f"{item} ")

    if not state:
        state = secrets.token_urlsafe(32)

    settings = get_settings()
    try:
        response = indieweb_utils.generate_auth_token(
            me,
            client_id,
            redirect_uri,
            response_type,
            state,
            code_challenge_method,
            final_scope,
            settings.session_key,
        )

        encoded_code = response.code
    except indieweb_utils.indieauth.server.AuthenticationError as exc:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                'error': 'invalid_request',
                'details': exc
            }
        )

    try:
        client_id_app = requests.get(client_id, timeout=5)
        h_app_item = indieweb_utils.get_h_app_item(client_id_app.text)
    except indieweb_utils.indieauth.happ.HAppNotFound:
        h_app_item = {}

    connection = sqlite3.connect(settings.token_db_path)

    with connection:
        cursor = connection.cursor()

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        already_issued_to_client = cursor.execute(
            "SELECT * FROM issued_tokens WHERE client_id = ?",
            (client_id,
            )
        ).fetchall()

        # delete tokens that have already been issued to the client
        # ensures that more than one token cannot be active per client
        if len(already_issued_to_client) > 0:
            cursor.execute("DELETE FROM issued_tokens WHERE client_id = ?", (client_id,))

        cursor.execute(
            "INSERT INTO issued_tokens VALUES (?, ?, ?, ?, ?, ?)",
            (
                encoded_code,
                me,
                now,
                client_id,
                int(time.time()) + 3600,
                json.dumps(asdict(h_app_item)),
            ),
        )

    if is_manually_issued and is_manually_issued == "true":
        flash_message(request, 'Your token was successfully issued.', 'success')
        flash_message(request, f"Your new token is: <code>{encoded_code}</code>", 'info')
        return RedirectResponse(
            status_code=HTTPStatus.SEE_OTHER,
            url=str(request.url_for('issued_page'))
        )

    if settings.webhook_server:
        data = {
            "message": f"{me} has issued an access token to {client_id}"
        }

        headers = {
            "Authorization": f"Bearer {settings.webhook_api_key}"
        }

        requests.post(
            settings.webhook_url,
            data=data,
            headers=headers,
            timeout=settings.rpc_timeout
        )

    return RedirectResponse(url=redirect_uri.strip("/") + f"?code={encoded_code}&state={state}")
