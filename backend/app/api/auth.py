"""Rotas de autenticacao."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

DbSession = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> User:
    existing = db.scalar(select(User).where(User.username == payload.username))
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username ja em uso")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Credenciais invalidas")

    token = create_access_token(subject=user.id, username=user.username)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expiration_hours * 3600,
    )


@router.get("/me", response_model=UserProfile)
def me(current_user: CurrentUser) -> User:
    return current_user
