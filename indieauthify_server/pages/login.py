"""
IndieAuthify: pages package; login page module
"""

from http import HTTPStatus

from fastapi.requests import Request
from fastapi.responses import JSONResponse, RedirectResponse, Response
import indieweb_utils

from indieauthify_server.dependencies.settings import get_settings
from indieauthify_server.dependencies.templates import get_template_engine
from indieauthify_server.dependencies.flash import flash_message


async def render_login_page(    # pylint: disable=too-many-return-statements
    request: Request,
    domain: str | None = None,
    redirect: str | None = None
) -> Response:
    """
    Render the login page
    """

    settings = get_settings()

    if redirect and redirect.split('/')[2].endswith(
        settings.me.strip('/').replace('https://',
                                       '').replace('http://',
                                                   '')
    ):
        request.session['user_redirect'] = redirect

    if request.session.get('rel_me_check'):
        return RedirectResponse(url=request.url_for('rel_page'))

    if request.session.get('me'):
        if request.session.get('user_redirect'):
            return RedirectResponse(url=str(request.session.get('user_redirect')))

        return RedirectResponse(url='/')

    args = {
        'request': request,
        'title': 'Login to the IndieAuthify server'
    }

    if request.method == 'POST':
        if not domain:
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={
                    'error': 'invalid_request',
                    'details': 'Missing domain parameter'
                }
            )

        domain_uri = domain.strip('/').replace('https://', '').replace('http://', '')
        me_uri = settings.me.strip('/').replace('https://', '').replace('http://', '')
        if domain_uri != me_uri:
            flash_message(request, 'Only approved domains can access this service', 'error')

            return RedirectResponse(
                status_code=HTTPStatus.SEE_OTHER,
                url=request.url_for('home_page')
            )

        request.session['rel_me_check'] = domain
        return RedirectResponse(status_code=HTTPStatus.SEE_OTHER, url=request.url_for('rel_page'))

    return get_template_engine().TemplateResponse('domain_login.html.j2', args)


async def render_rel_page(request: Request) -> Response:
    """
    Render the rel=me login page
    """

    if not request.session.get('rel_me_check'):
        return RedirectResponse(url=str(request.url_for('get_login_page')))

    if request.session.get('me'):
        if request.session.get('user_redirect'):
            return RedirectResponse(url=str(request.session.get('user_redirect')))

        return RedirectResponse(url='/')

    rel_me_links = indieweb_utils.get_valid_relmeauth_links(request.session.get('rel_me_check'))
    settings = get_settings()
    args = {
        'request': request,
        'rel_me_links': rel_me_links,
        'me': settings.me,
        'title': 'Authenticate with a rel=me link'
    }

    return get_template_engine().TemplateResponse('relme_login.html.j2', args)
