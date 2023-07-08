"""
IndieAuthify: routes module
"""

from typing import Annotated, Union

from fastapi import APIRouter, Form, Query
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

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
async def home_page(request: Request) -> HTMLResponse:
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
) -> HTMLResponse:
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
) -> HTMLResponse:
    """
    POST login page handler
    """

    return await render_login_page(request=request, domain=domain, redirect=redirect)


@router.get('/rel')
async def rel_page(request: Request) -> HTMLResponse:
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
async def get_authorize(  # pylint: disable=too-many-arguments
    request: Request,
    me: str | None = None,  # pylint: disable=invalid-name
    grant_type: str | None = None,
    code: str | None = None,
    client_id: str | None = None,
    redirect_uri: str | None = None,
    response_type: str | None = None,
    state: str | None = None,
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
    scope: str | None = None
) -> JSONResponse:
    """
    GET authorisation page handler
    """

    return await authorize_handler(
        request,
        me,
        grant_type,
        code,
        client_id,
        redirect_uri,
        response_type,
        state,
        code_challenge,
        code_challenge_method,
        scope
    )


@router.post('/auth')
async def post_authorize(     # pylint: disable=too-many-arguments
    _request: Request,
    grant_type: Annotated[str,
                          Form()],
    code: Annotated[str,
                    Form()],
    client_id: Annotated[str,
                         Form()],
    redirect_uri: Annotated[str,
                            Form()],
    code_challenge: Annotated[str,
                              Form()],
    code_challenge_method: Annotated[str,
                                     Form()]
) -> JSONResponse:
    """
    POST authorisation page handler
    """

    return await authorize_handler(
        grant_type,
        code,
        client_id,
        redirect_uri,
        code_challenge,
        code_challenge_method
    )


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
async def metadata(request: Request) -> JSONResponse:
    """
    Obtain metadata
    """

    return await metadata_handler(request)


@router.get('/.well-known/oauth-authorization-server')
async def oauth_authorization_server(request: Request) -> JSONResponse:
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
    me: Annotated[str,  # pylint: disable=invalid-name
                  Form()],
    client_id: Annotated[str,
                         Form()],
    redirect_uri: Annotated[str,
                            Form()],
    response_type: Annotated[str,
                             Form()],
    scope: Annotated[str,
                     Form()],
    is_manually_issued: Annotated[str,
                                  Form()],
    state: Annotated[str,
                     Form()] = None,
    code_challenge_method: Annotated[str,
                                     Form()] = None,
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


@router.get('token')
async def get_token_endpoint(request: Request) -> JSONResponse:
    """
    Issue token via GET
    """

    return await token_handler(request)


@router.post('token')
async def post_token_endpoint(     # pylint: disable=too-many-arguments
    request: Request,
    action: Annotated[str,
                      Form()],
    grant_type: Annotated[str,
                          Form()],
    code: Annotated[str,
                    Form()],
    client_id: Annotated[str,
                         Form()],
    redirect_uri: Annotated[str,
                            Form()],
    code_verifier: Annotated[str,
                             Form()]
):
    """
    Issue token via POST
    """

    return await token_form_handler(
        request,
        action,
        grant_type,
        code,
        client_id,
        redirect_uri,
        code_verifier
    )
