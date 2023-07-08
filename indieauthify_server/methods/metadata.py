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
    """

    body = {
        'authorization_endpoint': str(request.url_for('authorize')),
        'code_challenge_methods_supported': ['S256'],
        'grant_types_supported': ['authorization_code'],
        'issuer': str(request.url_for('authorize')),
        'response_models_supported': ['query'],
        'response_types_supported': ['code'],
        'scopes_supported': indieweb_utils.SCOPE_DEFINITIONS,
        'token_endpoint': str(request.url_for('token'))
    }

    return JSONResponse(status_code=HTTPStatus.OK, content=body)
