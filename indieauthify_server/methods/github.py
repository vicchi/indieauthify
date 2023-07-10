"""
IndieAuthify: methods package; GitHub authorization method handlers module
"""

import secrets

from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response
import indieweb_utils
import requests

from indieauthify_server.dependencies.settings import get_settings
from indieauthify_server.dependencies.flash import flash_message


async def github_auth_handler(request: Request) -> Response:
    """
    GitHub authorisation handler
    """

    state = secrets.token_urlsafe(32)
    request.session['github_state'] = state

    settings = get_settings()
    redirect_url = request.url_for('github_callback')
    url = f'https://github.com/login/oauth/authorize?client_id={settings.github_client_id}&redirect_uri={redirect_url}&state={state}'
    return RedirectResponse(url=url)


async def github_callback_handler(request: Request, code: str, state: str) -> Response:
    """
    GitHub authorisation callback handler
    """

    if state != request.session.get('github_state'):
        return RedirectResponse(url=str(request.url_for('get_login_page')))

    request.session.pop('github_state')
    headers = {
        'Accept': 'application/json'
    }

    settings = get_settings()
    redirect_url = request.url_for('github_callback')
    url = 'https://github.com/login/oauth/access_token'
    params = {
        'client_id': settings.github_client_id,
        'client_secret': settings.github_client_secret,
        'code': code,
        'redirect_uri': redirect_url
    }
    rsp = requests.post(url=url, params=params, headers=headers, timeout=settings.rpc_timeout)
    if not rsp.json().get('access_token'):
        flash_message(request, 'There was an error authenticating with GitHub.', 'error')
        return RedirectResponse(url=str(request.url_for('get_login_page')))

    user_request = requests.get(
        url='https://api.github.com/user',
        headers={"Authorization": f"token {rsp.json()['access_token']}"},
        timeout=settings.rpc_timeout
    )

    if user_request.status_code != 200:
        flash_message(request, 'There was an error authenticating with GitHub.', 'error')
        return RedirectResponse(url=str(request.url_for('get_login_page')))

    user = user_request.json()
    me = user.get('login')    # pylint: disable=invalid-name
    me_url = "https://github.com/" + me

    signed_in_with_correct_user = is_authenticated_as_allowed_user(me_url)

    if signed_in_with_correct_user is False:
        flash_message(request, 'You are not signed in with the correct user.', 'error')
        return RedirectResponse(url=str(request.url_for('get_login_page')))

    request.session['me'] = settings.me
    request.session['logged_in'] = True

    if request.session.get('user_redirect'):
        redirect_uri = str(request.session.get('user_redirect'))
        request.session.pop('user_redirect')
        return RedirectResponse(url=redirect_uri)

    return RedirectResponse(url=str(request.url_for('get_login_page')))


async def is_authenticated_as_allowed_user(me_url: str) -> bool:
    """
    Check if the allowed user has a valid rel=me link pointing to their domain.
    """

    settings = get_settings()
    home_me_links = indieweb_utils.get_valid_relmeauth_links(settings.me)

    for link in home_me_links:
        if link.strip('/') == me_url.strip('/'):
            return True

    return False
