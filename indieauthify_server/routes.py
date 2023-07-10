"""
IndieAuthify: routes module
"""

from typing import Annotated, Union

from fastapi import APIRouter, Form, Query
from fastapi.requests import Request
from fastapi.responses import Response

from indieauthify_server.models import AuthorizeParams, TokenParams
from indieauthify_server.methods.authorize import authorize_handler
from indieauthify_server.methods.github import github_auth_handler, github_callback_handler
from indieauthify_server.methods.metadata import metadata_handler
from indieauthify_server.methods.token import generate_token_handler, token_form_handler, token_handler
from indieauthify_server.pages.home import render_home_page
from indieauthify_server.pages.issued import render_issued_page
from indieauthify_server.pages.login import render_login_page, render_rel_page
from indieauthify_server.pages.logout import render_logout_page
from indieauthify_server.pages.revoke import render_revoke_page

router = APIRouter()


@router.get('/')
async def home_page(request: Request) -> Response:
    """
    Home page route handler
    """

    return await render_home_page(request)


@router.get('/login')
async def get_login_page(
    request: Request,
    redirect: Annotated[Union[str,
                              None],
                        Query(alias='r')] = None
) -> Response:
    """
    GET login page handler
    """

    return await render_login_page(request=request, redirect=redirect)


@router.post('/login')
async def post_login_page(
    request: Request,
    domain: Annotated[str,
                      Form()],
    redirect: Annotated[Union[str,
                              None],
                        Query(alias='r')] = None
) -> Response:
    """
    POST login page handler
    """

    return await render_login_page(request=request, domain=domain, redirect=redirect)


@router.get('/rel')
async def rel_page(request: Request) -> Response:
    """
    rel=me login page handler
    """

    return await render_rel_page(request=request)


@router.get('/logout')
async def logout_page(request: Request) -> Response:
    """
    Logout page handler
    """

    return await render_logout_page(request)


@router.get('/auth')
async def get_authorize(request: Request, params: AuthorizeParams) -> Response:
    """
    GET authorisation page handler
    """

    return await authorize_handler(request=request, params=params)


@router.post('/auth')
async def post_authorize(     # pylint: disable=too-many-arguments
    request: Request,
    params: AuthorizeParams
) -> Response:
    """
    POST authorisation page handler
    """

    return await authorize_handler(request=request, params=params)


@router.get('/auth/github')
async def github_authorize(request: Request) -> Response:
    """
    GitHub authorization
    """

    return await github_auth_handler(request)


@router.get('/auth/github/callback')
async def github_callback(request: Request, code: str, state: str) -> Response:
    """
    GitHub authorization callback
    """

    return await github_callback_handler(request, code, state)


@router.get('/metadata')
async def metadata(request: Request) -> Response:
    """
    Obtain metadata
    """

    return await metadata_handler(request)


@router.get('/.well-known/oauth-authorization-server')
async def oauth_authorization_server(request: Request) -> Response:
    """
    Obtain OAuth authorisation server metadata from well known URL
    """

    return await metadata_handler(request)


@router.get('/issued')
async def issued_page(
    request: Request,
    feed: str = 'false',
    authorization: str | None = None,
    token: str | None = None
) -> Response:
    """
    View issued tokens
    """

    return await render_issued_page(request, feed, authorization, token)


@router.post('/generate')
async def generate_token(     # pylint: disable=too-many-arguments
    request: Request,
    me: Annotated[str, Form()],    # pylint: disable=invalid-name
    client_id: Annotated[str, Form()],
    redirect_uri: Annotated[str, Form()],
    response_type: Annotated[str, Form()],
    scope: Annotated[str, Form()],
    is_manually_issued: Annotated[str, Form()],
    state: Annotated[Union[str, None], Form()] = None,
    code_challenge_method: Annotated[Union[str, None], Form()] = None
):
    """
    Generate token
    """

    return await generate_token_handler(
        request,
        me,
        client_id,
        redirect_uri,
        response_type,
        scope,
        is_manually_issued,
        state,
        code_challenge_method
    )


@router.get('/revoke')
async def revoke_token(request: Request, token: str | None = None) -> Response:
    """
    Revoke token
    """

    return await render_revoke_page(request, token)


@router.get('/token')
async def get_token_endpoint(request: Request) -> Response:
    """
    Issue token via GET
    """

    return await token_handler(request)


@router.post('/token')
async def post_token_endpoint(     # pylint: disable=too-many-arguments
    request: Request,
    params: TokenParams
) -> Response:
    """
    Issue token via POST
    """

    return await token_form_handler(request=request, params=params)
