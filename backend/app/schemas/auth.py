"""Schemas Pydantic de autenticacao."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# username: 3-32 caracteres alfanumericos
_USERNAME_PATTERN = r"^[a-zA-Z0-9]+$"


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=_USERNAME_PATTERN)
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    created_at: datetime
