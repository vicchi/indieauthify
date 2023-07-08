"""
IndieAuthify: methods package; authorize method handler module
"""

from http import HTTPStatus
from typing import Union
from urllib.parse import urlparse as parse_url

from bs4 import BeautifulSoup
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import indieweb_utils
import jwt
import requests

from indieauthify_server.dependencies.settings import get_settings
from indieauthify_server.dependencies.templates import get_template_engine
from indieauthify_server.dependencies.flash import flash_message


async def authorize_handler(    # pylint: disable=too-many-arguments,too-many-return-statements
    request: Request,
    me: Union[str,  # pylint: disable=invalid-name
              None] = None,
    grant_type: Union[str,
                      None] = None,
    code: Union[str,
                None] = None,
    client_id: Union[str,
                     None] = None,
    redirect_uri: Union[str,
                        None] = None,
    response_type: Union[str,
                         None] = None,
    state: Union[str,
                 None] = None,
    code_challenge: Union[str,
                          None] = None,
    code_challenge_method: Union[str,
                                 None] = None,
    scope: str | None = None
) -> Union[HTMLResponse,
           JSONResponse]:
    """
    Authorization method handler
    """

    if request.method == 'GET':
        if (me and me.strip('/') != request.session.get('me').strip('/')):
            request.session.pop('logged_in', None)
            request.session.pop('me', None)

            message = f"""
                {client_id} is requesting you to sign in as {me}.
                Please sign in as {me}.
                """

            flash_message(request, message, 'warning')
            return RedirectResponse(url=str(request.url_for('get_login_page',
                                                            {'r': request.url})))

        if request.session.get("logged_in") is not True:
            return RedirectResponse(url=str(request.url_for('get_login_page',
                                                            {'r': request.url})))

        if not client_id or not redirect_uri or not response_type or not state:
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={'error': 'invalid_request'}
            )

        if response_type not in ('code', 'id'):
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={'error': 'invalid_request'}
            )

        settings = get_settings()
        try:
            client_id_app = requests.get(client_id, timeout=settings.rpc_timeout)
        except requests.RequestException as exc:
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={
                    'error': 'invalid_request',
                    'details': exc
                }
            )

        h_app_item = None

        redirect_uri_domain = parse_url(redirect_uri).netloc
        client_id_domain = parse_url(client_id).netloc

        redirect_uri_scheme = parse_url(redirect_uri).scheme
        client_id_scheme = parse_url(client_id).scheme

        if (redirect_uri_domain != client_id_domain or redirect_uri_scheme != client_id_scheme):
            fetch_client = requests.get(client_id, timeout=settings.rpc_timeout)

            confirmed_redirect_uri = False

            links = indieweb_utils.discover_endpoints(client_id, ['redirect_uri'])

            for url in links:
                if url.startswith('/'):
                    url = redirect_uri_scheme + redirect_uri_domain.strip('/') + url

                if url == redirect_uri:
                    confirmed_redirect_uri = True

            link_tags = BeautifulSoup(fetch_client.text, 'lxml').find_all('link')

            for link in link_tags:
                if link.get('rel') == 'redirect_uri':
                    url = link.get('href')

                    if url.startswith('/'):
                        url = redirect_uri_scheme + redirect_uri_domain.strip('/') + url

                    if url == redirect_uri:
                        confirmed_redirect_uri = True

            if not confirmed_redirect_uri:
                return JSONResponse(
                    status_code=HTTPStatus.BAD_REQUEST,
                    content={'error': 'invalid_request'}
                )

        if client_id_app.status_code == 200:
            h_app_item = indieweb_utils.get_h_app_item(client_id_app.text)

        args = {
            'request': request,
            'scope': scope,
            'me': me,
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': response_type,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': code_challenge_method,
            'h_app_item': h_app_item,
            'SCOPE_DEFINITIONS': indieweb_utils.SCOPE_DEFINITIONS,
            'title': f"Authenticate to {client_id.replace('https://', '').replace('http://', '').strip()}"
        }

        return get_template_engine().TemplateResponse('confirm_auth.html.j2', args)

    try:
        indieweb_utils.validate_authorization_response(
            grant_type,
            code,
            client_id,
            redirect_uri,
            code_challenge,
            code_challenge_method,
        )
    except indieweb_utils.indieauth.server.TokenValidationError as exc:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                'error': exc,
                'details': exc
            }
        )

    settings = get_settings()
    try:
        decoded_code = jwt.decode(code, settings.session_key, algorithms=['HS256'])
    except jwt.DecodeError as exc:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                'error': 'invalid_grant',
                'details': exc
            }
        )

    try:
        indieweb_utils.indieauth.server._verify_decoded_code(   # pylint: disable=protected-access
            client_id,
            redirect_uri,
            decoded_code['client_id'],
            decoded_code['redirect_uri'],
            decoded_code['expires'],
        )
    except indieweb_utils.indieauth.server.AuthorizationCodeExpiredError as exc:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                'error': 'invalid_request',
                'details': exc
            }
        )
    except indieweb_utils.indieauth.server.TokenValidationError as exc:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                'error': 'invalid_request',
                'details': exc
            }
        )

    return JSONResponse(
        status_code=HTTPStatus.OK,
        content={'me': decoded_code['me'].strip('/') + '/'}
    )
