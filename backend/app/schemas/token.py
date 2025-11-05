"""
Token schemas for authentication
"""
from pydantic import BaseModel


class Token(BaseModel):
    """
    JWT token response model
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    JWT token payload data
    """
    username: str | None = None
