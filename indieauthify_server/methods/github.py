"""
IndieAuthify: methods package; GitHub authorization method handlers module
"""

import logging
import secrets

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi.requests import Request
from fastapi.responses import RedirectResponse, Response
import indieweb_utils
from pydantic import HttpUrl

from indieauthify_server.dependencies.settings import get_settings
from indieauthify_server.dependencies.flash import flash_message

settings = get_settings()
oauth = OAuth()
github = oauth.register(
    name='github',
    client_id=settings.github_client_id,
    client_secret=settings.github_client_secret,
    access_token_url=settings.github_token_url,
    access_token_params=None,
    authorize_url=settings.github_authorize_url,
    authorize_params=None,
    api_base_url=settings.github_base_url,
    client_kwargs={'scope': 'user:email'}
)


async def github_login_handler(request: Request) -> Response:
    """
    GitHub login handler
    """

    logging.debug('%s %s - github_login_handler', request.method, request.url.path)
    state = secrets.token_urlsafe(32)
    request.session['github_state'] = state
    redirect_uri = str(request.url_for('github_callback'))
    logging.debug(
        '%s: login requested, bouncing to GitHub and back to %s',
        request.url.path,
        redirect_uri
    )
    return await oauth.github.authorize_redirect(request, redirect_uri, state=state)


async def github_authenticate_handler(request: Request, state: str) -> Response:
    """
    GitHub authorisation callback handler
    """

    logging.debug('%s %s - github_authenticate_handler', request.method, request.url.path)
    if state != request.session.get('github_state'):
        logging.error('%s: GitHub state token mismatch; bouncing to login page', request.url.path)
        flash_message(request, 'A GitHub state token mismatch was found', 'error')
        return RedirectResponse(url=str(request.url_for('get_login_page')))

    request.session.pop('github_state')

    logging.debug('%s: GitHub says yes, getting access token', request.url.path)
    try:
        token = await oauth.github.authorize_access_token(request)
        logging.debug('%s: got access token, getting user profile', request.url.path)

        rsp = await oauth.github.get('user', token=token)
        profile = rsp.json()

        profile_name = profile.get('login')    # pylint: disable=invalid-name
        profile_url = f'https://github.com/{profile_name}'

        logging.debug('%s: almost there, checking user profile', request.url.path)
        signed_in_with_correct_user = await is_authenticated_as_allowed_user(
            settings.me,
            profile_url
        )

        if not signed_in_with_correct_user:
            flash_message(request, 'You are not signed in with the correct user.', 'error')
            return RedirectResponse(url=str(request.url_for('get_login_page')))

        request.session['me'] = settings.me
        request.session['logged_in'] = True
        flash_message(request, f'Authenticated successfully as {profile_url}', 'success')

        if request.session.get('user_redirect'):
            redirect_uri = str(request.session.get('user_redirect'))
            request.session.pop('user_redirect')
            logging.debug('%s: success, bouncing to %s', request.url.path, redirect_uri)
            return RedirectResponse(url=redirect_uri)

        logging.debug('%s: success, bouncing to login page', request.url.path)
        return RedirectResponse(url=str(request.url_for('get_login_page')))

    except OAuthError as exc:
        logging.error('%s: GitHub says no (OAuthError) %s', request.url.path, exc)
        flash_message(request, exc, 'error')
        return RedirectResponse(url=str(request.url_for('get_login_page')))


async def is_authenticated_as_allowed_user(me_domain: HttpUrl, profile_url: str) -> bool:
    """
    Check if the allowed user has a valid rel=me link pointing to their domain.
    """

    home_me_links = indieweb_utils.get_valid_relmeauth_links(me_domain)

    for link in home_me_links:
        if link.strip('/') == profile_url.strip('/'):
            return True

    return False
