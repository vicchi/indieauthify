"""
IndieAuthify: models module
"""

from typing import Annotated

from fastapi import Form
from pydantic import BaseModel


class AuthorizeParams(BaseModel):
    """
    /auth query string parameters
    """

    me: str    # pylint: disable=invalid-name
    code: str
    grant_type: str | None = None
    client_id: str | None = None
    redirect_uri: str | None = None
    response_type: str | None = None
    state: str | None = None
    code_challenge: str | None = None
    code_challenge_method: str | None = None
    scope: str | None = None


# class GenerateParams(BaseModel):
#     """
#     /generate query string parameters
#     """

#     me: Annotated[str, Form()]    # pylint: disable=invalid-name
#     client_id: Annotated[str, Form()]
#     redirect_uri: Annotated[str, Form()]
#     response_type: Annotated[str, Form()]
#     scope: Annotated[str, Form()]
#     is_manually_issued: Annotated[str, Form()]
#     state: Annotated[Union[str, None], Form()] = None
#     code_challenge_method: Annotated[Union[str, None], Form()] = None


class TokenParams(BaseModel):
    """
    /token query string parameters
    """

    action: Annotated[str, Form()]
    grant_type: Annotated[str, Form()]
    code: Annotated[str, Form()]
    client_id: Annotated[str, Form()]
    redirect_uri: Annotated[str, Form()]
    code_verifier: Annotated[str, Form()]
