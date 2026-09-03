"""Gestao de sessoes em memoria + pool de conexoes WebSocket (F3.2, F4.3).

`SessionManager` e um Singleton. Sessoes e chaves nunca sao persistidas: existem
apenas enquanto a sessao esta ativa. Ao encerrar, a chave e sobrescrita com zeros
antes de ser liberada (F3.6).
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING

from app.crypto.key_protocol import ProtocolMode

if TYPE_CHECKING:
    from fastapi import WebSocket


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SessionState(str, Enum):
    PENDING = "pending"  # Alice solicitou; aguardando Bob
    ESTABLISHING = "establishing"  # Bob aceitou; troca de chave em curso
    ACTIVE = "active"  # chave estabelecida; chat liberado
    REJECTED = "rejected"  # Bob recusou
    CLOSED = "closed"  # encerrada normalmente
    ABORTED = "aborted"  # encerrada por anomalia (ex.: eve_detected)


_TERMINAL_STATES = {SessionState.REJECTED, SessionState.CLOSED, SessionState.ABORTED}


@dataclass
class Session:
    """Sessao de chat — nunca persistida em banco."""

    id: str
    alice_id: str
    bob_id: str
    mode: ProtocolMode
    state: SessionState = SessionState.PENDING
    key: bytearray | None = None
    qber: float | None = None
    created_at: datetime = field(default_factory=_utc_now)
    last_activity: datetime = field(default_factory=_utc_now)

    def involves(self, user_id: str) -> bool:
        return user_id in (self.alice_id, self.bob_id)

    def peer_of(self, user_id: str) -> str:
        return self.bob_id if user_id == self.alice_id else self.alice_id

    def touch(self) -> None:
        self.last_activity = _utc_now()

    @property
    def is_terminal(self) -> bool:
        return self.state in _TERMINAL_STATES


class SessionError(Exception):
    """Operacao invalida sobre uma sessao."""


class SessionManager:
    """Singleton que gerencia sessoes ativas e o pool de conexoes WebSocket."""

    _instance: SessionManager | None = None
    _singleton_lock = threading.Lock()

    def __new__(cls) -> SessionManager:
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialize()
                    cls._instance = instance
        return cls._instance

    def _initialize(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._connections: dict[str, set[WebSocket]] = {}
        self._mutex = threading.Lock()

    # ----------------------------------------------------------------- sessoes
    def create_session(self, alice_id: str, bob_id: str, mode: ProtocolMode) -> Session:
        if alice_id == bob_id:
            raise SessionError("Nao e possivel abrir sessao consigo mesmo")
        session = Session(
            id=str(uuid.uuid4()),
            alice_id=alice_id,
            bob_id=bob_id,
            mode=mode,
        )
        with self._mutex:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        with self._mutex:
            return self._sessions.get(session_id)

    def list_for_user(self, user_id: str) -> list[Session]:
        with self._mutex:
            return [s for s in self._sessions.values() if s.involves(user_id)]

    def accept(self, session_id: str, user_id: str) -> Session:
        with self._mutex:
            session = self._require(session_id)
            if user_id != session.bob_id:
                raise SessionError("Apenas o destinatario pode aceitar a sessao")
            if session.state != SessionState.PENDING:
                raise SessionError(f"Sessao nao esta pendente (estado: {session.state.value})")
            session.state = SessionState.ESTABLISHING
            session.touch()
            return session

    def reject(self, session_id: str, user_id: str) -> Session:
        with self._mutex:
            session = self._require(session_id)
            if user_id != session.bob_id:
                raise SessionError("Apenas o destinatario pode recusar a sessao")
            if session.state != SessionState.PENDING:
                raise SessionError(f"Sessao nao esta pendente (estado: {session.state.value})")
            session.state = SessionState.REJECTED
            session.touch()
            return session

    def set_key(self, session_id: str, key: bytes, qber: float | None = None) -> Session:
        with self._mutex:
            session = self._require(session_id)
            session.key = bytearray(key)
            session.qber = qber
            session.state = SessionState.ACTIVE
            session.touch()
            return session

    def close_session(
        self, session_id: str, reason: str = "closed", user_id: str | None = None
    ) -> Session:
        with self._mutex:
            session = self._require(session_id)
            if user_id is not None and not session.involves(user_id):
                raise SessionError("Usuario nao participa desta sessao")
            self._wipe_key(session)
            session.state = (
                SessionState.ABORTED if reason == "eve_detected" else SessionState.CLOSED
            )
            session.touch()
            return session

    def cleanup_expired(self, timeout_minutes: int) -> list[str]:
        """Encerra sessoes inativas alem do timeout (F3.7). Retorna os ids encerrados."""
        cutoff = _utc_now() - timedelta(minutes=timeout_minutes)
        expired: list[str] = []
        with self._mutex:
            for session in self._sessions.values():
                if session.is_terminal:
                    continue
                if session.last_activity < cutoff:
                    self._wipe_key(session)
                    session.state = SessionState.CLOSED
                    expired.append(session.id)
        return expired

    def _require(self, session_id: str) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionError("Sessao nao encontrada")
        return session

    @staticmethod
    def _wipe_key(session: Session) -> None:
        """Sobrescreve a chave com zeros antes de liberar a referencia (F3.6)."""
        if session.key is not None:
            for i in range(len(session.key)):
                session.key[i] = 0
            session.key = None

    # ------------------------------------------------------- pool de conexoes
    def register_connection(self, user_id: str, websocket: WebSocket) -> None:
        with self._mutex:
            self._connections.setdefault(user_id, set()).add(websocket)

    def unregister_connection(self, user_id: str, websocket: WebSocket) -> None:
        with self._mutex:
            sockets = self._connections.get(user_id)
            if sockets is not None:
                sockets.discard(websocket)
                if not sockets:
                    del self._connections[user_id]

    def connections_for(self, user_id: str) -> list[WebSocket]:
        with self._mutex:
            return list(self._connections.get(user_id, ()))

    def online_user_ids(self) -> set[str]:
        with self._mutex:
            return set(self._connections.keys())


def get_session_manager() -> SessionManager:
    """Dependencia FastAPI: retorna a instancia unica do SessionManager."""
    return SessionManager()
