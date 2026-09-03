"""Observers do monitor de QBER — padrao Observer (F12.2, F12.3).

Cada observer implementa ``on_event(event: dict)``. O `QBERMonitor` (Subject)
notifica todos os observers a cada medicao de QBER.
"""

from __future__ import annotations

import contextlib
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from app.core.event_logging import EVENT_EVE_DETECTED, log_event
from app.core.session_manager import SessionError
from app.schemas.ws import WSMessage, WSMessageType

if TYPE_CHECKING:
    from app.core.session_manager import Session, SessionManager


class Observer(ABC):
    """Contrato comum dos observers do monitor de QBER (F12.3)."""

    @abstractmethod
    def on_event(self, event: dict[str, Any]) -> None: ...


class Logger(Observer):
    """Registra cada evento de QBER em log estruturado JSON."""

    def __init__(self, mode: str | None = None) -> None:
        self._mode = mode

    def on_event(self, event: dict[str, Any]) -> None:
        log_event(
            event["type"],
            session_id=event.get("session_id"),
            mode=self._mode,
            qber=event.get("qber"),
            threshold=event.get("threshold"),
            exceeded=event.get("exceeded"),
        )


class NotificationService(Observer):
    """Prepara mensagens WSS `qber_alert` para o frontend quando ha espionagem.

    As mensagens sao acumuladas em `pending` e enviadas pelo chamador (que opera
    em contexto assincrono) via `drain()`.
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self.pending: list[tuple[str, WSMessage]] = []

    def on_event(self, event: dict[str, Any]) -> None:
        if event.get("type") != EVENT_EVE_DETECTED:
            return
        message = WSMessage(
            type=WSMessageType.QBER_ALERT,
            session_id=event.get("session_id"),
            payload={
                "qber": event.get("qber"),
                "threshold": event.get("threshold"),
                "detail": "QBER acima do limiar — possivel espionagem detectada",
            },
        )
        for user_id in (self._session.alice_id, self._session.bob_id):
            self.pending.append((user_id, message))

    def drain(self) -> list[tuple[str, WSMessage]]:
        """Retorna e limpa as mensagens pendentes."""
        messages = self.pending
        self.pending = []
        return messages


class SessionTerminator(Observer):
    """Encerra a sessao quando o QBER ultrapassa o limiar (F12.2)."""

    def __init__(self, manager: SessionManager) -> None:
        self._manager = manager

    def on_event(self, event: dict[str, Any]) -> None:
        if event.get("type") != EVENT_EVE_DETECTED:
            return
        session_id = event.get("session_id")
        if session_id is None:
            return
        # A sessao pode ja ter sido encerrada por outro caminho.
        with contextlib.suppress(SessionError):
            self._manager.close_session(session_id, reason="eve_detected")
