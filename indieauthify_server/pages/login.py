"""
IndieAuthify: pages package; login page module
"""

from http import HTTPStatus
import logging

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

    logging.debug('%s %s - render_login_page', request.method, request.url.path)
    logging.debug('domain: %s redirect: %s', domain, redirect)
    settings = get_settings()

    if redirect and redirect.split('/')[2].endswith(
        settings.me.strip('/').replace('https://',
                                       '').replace('http://',
                                                   '')
    ):
        logging.debug('setting session.user_redirect to %s', redirect)
        request.session['user_redirect'] = redirect

    if request.session.get('rel_me_check'):
        logging.debug('found session.rel_me_check, bouncing to %s', request.url_for('rel_page'))
        return RedirectResponse(url=request.url_for('rel_page'))

    if request.session.get('me'):
        if request.session.get('user_redirect'):
            logging.debug(
                'found session.me and session.user_redirect, bouncing to %s',
                request.session.get('user_redirect')
            )
            return RedirectResponse(url=str(request.session.get('user_redirect')))

        logging.debug('found session.me and not session.user_redirect, bouncing to /')
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
        logging.debug(
            'setting session.rel_me_check to %s and bouncing to %s',
            domain,
            request.url_for('rel_page')
        )
        return RedirectResponse(status_code=HTTPStatus.SEE_OTHER, url=request.url_for('rel_page'))

    template = 'domain_login.html.j2'
    logging.debug('rendering %s', template)
    return get_template_engine().TemplateResponse(template, args)


async def render_rel_page(request: Request) -> Response:
    """
    Render the rel=me login page
    """

    logging.debug('%s %s - render_rel_page', request.method, request.url.path)

    if not request.session.get('rel_me_check'):
        logging.debug(
            'missing session.rel_me_check, bouncing to %s',
            request.session.get('get_login_page')
        )
        return RedirectResponse(url=str(request.url_for('get_login_page')))

    if request.session.get('me'):
        if request.session.get('user_redirect'):
            logging.debug(
                'found session.me and session.user_redirect, bouncing to %s',
                request.session.get('user_redirect')
            )
            return RedirectResponse(url=str(request.session.get('user_redirect')))

        logging.debug('found session.me and not session.user_redirect, bouncing to /')
        return RedirectResponse(url='/')

    logging.debug('getting rel=me links for %s', request.session.get('rel_me_check'))
    rel_me_links = indieweb_utils.get_valid_relmeauth_links(
        request.session.get('rel_me_check'),
        require_rel_me_link_back=True
    )
    logging.debug('received rel=me links: %s', rel_me_links)
    settings = get_settings()
    args = {
        'request': request,
        'rel_me_links': rel_me_links,
        'me': settings.me,
        'title': 'Authenticate with a rel=me link'
    }

    template = 'relme_login.html.j2'
    logging.debug('rendering %s', template)
    return get_template_engine().TemplateResponse(template, args)
