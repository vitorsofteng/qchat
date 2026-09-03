"""Schemas Pydantic de sessao."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from app.crypto.key_protocol import ProtocolMode

if TYPE_CHECKING:
    from app.core.session_manager import Session


class SessionRequestBody(BaseModel):
    bob_username: str = Field(min_length=3, max_length=32)
    mode: ProtocolMode


class SessionKeyView(BaseModel):
    """Chave de sessao recuperada por um participante autenticado."""

    key: str  # chave de 32 bytes, codificada em base64
    qber: float | None = None


class SessionView(BaseModel):
    id: str
    alice_id: str
    bob_id: str
    mode: ProtocolMode
    state: str
    qber: float | None = None
    created_at: datetime

    @classmethod
    def from_session(cls, session: Session) -> SessionView:
        return cls(
            id=session.id,
            alice_id=session.alice_id,
            bob_id=session.bob_id,
            mode=session.mode,
            state=session.state.value,
            qber=session.qber,
            created_at=session.created_at,
        )
