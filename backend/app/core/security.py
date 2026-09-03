"""Hashing de senha (bcrypt) e tokens JWT."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings

settings = get_settings()

# bcrypt opera sobre no maximo 72 bytes; o schema de registro limita a senha.
_BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    password = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    salt = bcrypt.gensalt(rounds=settings.bcrypt_cost)
    return bcrypt.hashpw(password, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    password = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(password, hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(*, subject: str, username: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "username": username,
        "iat": now,
        "exp": now + timedelta(hours=settings.jwt_expiration_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Decodifica e valida o JWT. Lanca jwt.InvalidTokenError em caso de falha."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
