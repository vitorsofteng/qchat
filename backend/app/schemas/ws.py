"""Protocolo de mensagens WebSocket (F4.2).

Toda mensagem trafega como JSON no formato {type, session_id, payload}.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class WSMessageType(str, Enum):
    # Ciclo de vida da sessao
    SESSION_REQUEST = "session_request"
    SESSION_ACCEPTED = "session_accepted"
    SESSION_REJECTED = "session_rejected"
    SESSION_CLOSED = "session_closed"
    # Estabelecimento de chave
    KEY_EXCHANGE = "key_exchange"
    KEY_ESTABLISHED = "key_established"
    # Mensagens de chat (envelope cifrado AES-256-GCM)
    CHAT_MESSAGE = "chat_message"
    # Indicador de digitacao
    TYPING = "typing"
    # Monitoramento
    QBER_ALERT = "qber_alert"
    # Infraestrutura
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


class WSMessage(BaseModel):
    type: WSMessageType
    session_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


def error_message(detail: str, session_id: str | None = None) -> WSMessage:
    return WSMessage(
        type=WSMessageType.ERROR,
        session_id=session_id,
        payload={"detail": detail},
    )
