"""
IndieAuthify: methods package; authorize method handler module
"""

from http import HTTPStatus
from urllib.parse import urlparse as parse_url

from bs4 import BeautifulSoup
from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
import indieweb_utils
import jwt
import requests

from indieauthify_server.dependencies.settings import get_settings
from indieauthify_server.dependencies.templates import get_template_engine
from indieauthify_server.dependencies.flash import flash_message
from indieauthify_server.models import AuthorizeParams


async def authorize_handler(    # pylint: disable=too-many-arguments,too-many-return-statements
    request: Request,
    params: AuthorizeParams
) -> Response:
    """
    Authorization method handler
    GET POST /auth
    """

    if request.method == 'GET':

        domain_uri = params.me
        session_uri = request.session.get('me')
        if domain_uri and session_uri and domain_uri.strip('/') != session_uri.strip('/'):
            request.session.pop('logged_in', None)
            request.session.pop('me', None)

            message = f"""
                {params.client_id} is requesting you to sign in as {params.me}.
                Please sign in as {params.me}.
                """

            flash_message(request, message, 'warning')
            return RedirectResponse(
                url=str(request.url_for('get_login_page',
                                        **{'r': request.url}))
            )

        if request.session.get("logged_in") is not True:
            return RedirectResponse(
                url=str(request.url_for('get_login_page',
                                        **{'r': request.url}))
            )

        if not params.client_id or not params.redirect_uri or not params.response_type or not params.state:
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={'error': 'invalid_request'}
            )

        if params.response_type not in ('code', 'id'):
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={'error': 'invalid_request'}
            )

        settings = get_settings()
        try:
            client_id_app = requests.get(params.client_id, timeout=settings.rpc_timeout)
        except requests.RequestException as exc:
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={
                    'error': 'invalid_request',
                    'details': exc
                }
            )

        h_app_item = None

        redirect_uri_domain = parse_url(params.redirect_uri).netloc
        client_id_domain = parse_url(params.client_id).netloc

        redirect_uri_scheme = parse_url(params.redirect_uri).scheme
        client_id_scheme = parse_url(params.client_id).scheme

        if (redirect_uri_domain != client_id_domain or redirect_uri_scheme != client_id_scheme):
            fetch_client = requests.get(params.client_id, timeout=settings.rpc_timeout)

            confirmed_redirect_uri = False

            links = indieweb_utils.discover_endpoints(params.client_id, ['redirect_uri'])

            for url in links:
                if url.startswith('/'):
                    url = redirect_uri_scheme + redirect_uri_domain.strip('/') + url

                if url == params.redirect_uri:
                    confirmed_redirect_uri = True

            link_tags = BeautifulSoup(fetch_client.text, 'lxml').find_all('link')

            for link in link_tags:
                if link.get('rel') == 'redirect_uri':
                    url = link.get('href')

                    if url.startswith('/'):
                        url = redirect_uri_scheme + redirect_uri_domain.strip('/') + url

                    if url == params.redirect_uri:
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
            'scope': params.scope,
            'me': params.me,
            'client_id': params.client_id,
            'redirect_uri': params.redirect_uri,
            'response_type': params.response_type,
            'state': params.state,
            'code_challenge': params.code_challenge,
            'code_challenge_method': params.code_challenge_method,
            'h_app_item': h_app_item,
            'SCOPE_DEFINITIONS': indieweb_utils.SCOPE_DEFINITIONS,
            'title': f"Authenticate to {params.client_id.replace('https://', '').replace('http://', '').strip()}"
        }

        return get_template_engine().TemplateResponse('confirm_auth.html.j2', args)

    try:
        indieweb_utils.validate_authorization_response(
            params.grant_type,
            params.code,
            params.client_id,
            params.redirect_uri,
            params.code_challenge,
            params.code_challenge_method,
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
        decoded_code = jwt.decode(params.code, settings.session_key, algorithms=['HS256'])
    except jwt.DecodeError as exc:
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                'error': 'invalid_grant',
                'details': exc
            }
        )

    try:
        indieweb_utils.indieauth.server.verify_decoded_code(
            params.client_id,
            params.redirect_uri,
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
