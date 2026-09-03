"""Rotas de gestao de sessoes (F3.3 - F3.6)."""

import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from app.api.deps import CurrentUser
from app.api.notifications import send_to_user
from app.core.database import get_db
from app.core.event_logging import EVENT_SESSION_CLOSED, EVENT_SESSION_CREATED, log_event
from app.core.key_exchange import establish_session_key
from app.core.session_manager import (
    SessionError,
    SessionManager,
    SessionState,
    get_session_manager,
)
from app.models.user import User
from app.schemas.session import SessionKeyView, SessionRequestBody, SessionView
from app.schemas.ws import WSMessage, WSMessageType

router = APIRouter(prefix="/sessions", tags=["sessions"])

Db = Annotated[DbSession, Depends(get_db)]
Manager = Annotated[SessionManager, Depends(get_session_manager)]


def _require_session(manager: SessionManager, session_id: str, user: User):
    session = manager.get(session_id)
    if session is None or not session.involves(user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Sessao nao encontrada")
    return session


@router.post("/request", response_model=SessionView, status_code=status.HTTP_201_CREATED)
async def request_session(
    body: SessionRequestBody, current_user: CurrentUser, db: Db, manager: Manager
) -> SessionView:
    bob = db.scalar(select(User).where(User.username == body.bob_username))
    if bob is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Destinatario nao encontrado")
    try:
        session = manager.create_session(current_user.id, bob.id, body.mode)
    except SessionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    log_event(
        EVENT_SESSION_CREATED,
        session_id=session.id,
        mode=session.mode.value,
        alice=current_user.username,
        bob=bob.username,
    )
    await send_to_user(
        bob.id,
        WSMessage(
            type=WSMessageType.SESSION_REQUEST,
            session_id=session.id,
            payload={"from": current_user.username, "mode": session.mode.value},
        ),
    )
    return SessionView.from_session(session)


@router.post("/{session_id}/accept", response_model=SessionView)
async def accept_session(
    session_id: str, current_user: CurrentUser, manager: Manager
) -> SessionView:
    try:
        session = manager.accept(session_id, current_user.id)
    except SessionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await send_to_user(
        session.alice_id,
        WSMessage(type=WSMessageType.SESSION_ACCEPTED, session_id=session.id, payload={}),
    )
    # Estabelecimento de chave: executado pelo servidor e distribuido via WSS.
    await establish_session_key(session, manager)
    return SessionView.from_session(session)


@router.post("/{session_id}/reject", response_model=SessionView)
async def reject_session(
    session_id: str, current_user: CurrentUser, manager: Manager
) -> SessionView:
    try:
        session = manager.reject(session_id, current_user.id)
    except SessionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await send_to_user(
        session.alice_id,
        WSMessage(type=WSMessageType.SESSION_REJECTED, session_id=session.id, payload={}),
    )
    return SessionView.from_session(session)


@router.delete("/{session_id}", response_model=SessionView)
async def close_session(
    session_id: str, current_user: CurrentUser, manager: Manager
) -> SessionView:
    session = _require_session(manager, session_id, current_user)
    try:
        session = manager.close_session(session_id, reason="closed", user_id=current_user.id)
    except SessionError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    log_event(
        EVENT_SESSION_CLOSED,
        session_id=session.id,
        mode=session.mode.value,
        reason="closed",
    )
    await send_to_user(
        session.peer_of(current_user.id),
        WSMessage(type=WSMessageType.SESSION_CLOSED, session_id=session.id, payload={}),
    )
    return SessionView.from_session(session)


@router.get("", response_model=list[SessionView])
def list_sessions(current_user: CurrentUser, manager: Manager) -> list[SessionView]:
    return [SessionView.from_session(s) for s in manager.list_for_user(current_user.id)]


@router.get("/{session_id}", response_model=SessionView)
def get_session(session_id: str, current_user: CurrentUser, manager: Manager) -> SessionView:
    return SessionView.from_session(_require_session(manager, session_id, current_user))


@router.get("/{session_id}/key", response_model=SessionKeyView)
def get_session_key(session_id: str, current_user: CurrentUser, manager: Manager) -> SessionKeyView:
    """Recupera a chave de uma sessao ativa (ex.: apos o cliente recarregar a pagina).

    A chave e entregue apenas a participantes autenticados, pelo canal TLS — a
    mesma postura de seguranca da distribuicao via WSS.
    """
    session = _require_session(manager, session_id, current_user)
    if session.state != SessionState.ACTIVE or session.key is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Chave de sessao ainda nao estabelecida"
        )
    return SessionKeyView(
        key=base64.b64encode(bytes(session.key)).decode("ascii"),
        qber=session.qber,
    )
