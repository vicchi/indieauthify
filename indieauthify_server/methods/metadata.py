"""
IndieAuthify: methods package; metadata method handler module
"""

from http import HTTPStatus

from fastapi.requests import Request
from fastapi.responses import JSONResponse
import indieweb_utils


async def metadata_handler(request: Request) -> JSONResponse:
    """
    Metadata endpoint and well known URL handler
    GET /metadata
    GET /.well-known/oauth-authorization-server
    """

    body = {
        'issuer': str(request.url_for('get_authorize')),
        'authorization_endpoint': str(request.url_for('get_authorize')),
        'token_endpoint': str(request.url_for('generate_token')),
        'revocation_endpoint': str(request.url_for('revoke_token')),
        'scopes_supported': indieweb_utils.SCOPE_DEFINITIONS,
        'response_types_supported': ['code'],
        'response_models_supported': ['query'],
        'grant_types_supported': ['authorization_code'],
        'service_documentation': 'https://indieauth.spec.indieweb.org/',
        'code_challenge_methods_supported': ['S256']
    }

    return JSONResponse(status_code=HTTPStatus.OK, content=body)
