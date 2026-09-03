"""Endpoint WebSocket e canal classico (F4)."""

from __future__ import annotations

import asyncio
import contextlib
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jwt import InvalidTokenError
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.event_logging import EVENT_MESSAGE_RECEIVED, EVENT_MESSAGE_SENT, log_event
from app.core.security import decode_access_token
from app.core.session_manager import SessionManager, SessionState
from app.schemas.ws import WSMessage, WSMessageType, error_message

router = APIRouter(tags=["websocket"])
settings = get_settings()

# Codigos de fechamento WS na faixa de aplicacao (4000-4999).
_WS_UNAUTHORIZED = 4401

_RELAY_TYPES = {
    WSMessageType.CHAT_MESSAGE,
    WSMessageType.KEY_EXCHANGE,
    WSMessageType.TYPING,
}


async def _send(websocket: WebSocket, message: WSMessage) -> None:
    await websocket.send_json(message.model_dump(mode="json"))


async def _heartbeat(websocket: WebSocket) -> None:
    """Envia ping periodico para detectar conexoes mortas (F4.4)."""
    ping = WSMessage(type=WSMessageType.PING)
    try:
        while True:
            await asyncio.sleep(settings.ws_heartbeat_seconds)
            await _send(websocket, ping)
    except (WebSocketDisconnect, RuntimeError):
        return


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str) -> None:
    """Conexao WSS autenticada por JWT no path (F4.1)."""
    try:
        payload = decode_access_token(token)
        user_id = str(payload["sub"])
    except (InvalidTokenError, KeyError):
        await websocket.close(code=_WS_UNAUTHORIZED)
        return

    await websocket.accept()
    manager = SessionManager()
    manager.register_connection(user_id, websocket)
    heartbeat_task = asyncio.create_task(_heartbeat(websocket))

    try:
        while True:
            try:
                raw = await websocket.receive_json()
            except json.JSONDecodeError:
                await _send(websocket, error_message("Payload nao e JSON valido"))
                continue
            await _handle_message(user_id, websocket, manager, raw)
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task
        manager.unregister_connection(user_id, websocket)


async def _handle_message(
    user_id: str, websocket: WebSocket, manager: SessionManager, raw: dict
) -> None:
    from app.api.notifications import send_to_user

    try:
        message = WSMessage.model_validate(raw)
    except ValidationError:
        await _send(websocket, error_message("Mensagem WS malformada"))
        return

    if message.type == WSMessageType.PING:
        await _send(websocket, WSMessage(type=WSMessageType.PONG))
        return
    if message.type == WSMessageType.PONG:
        return  # ack de heartbeat

    if message.type in _RELAY_TYPES:
        session = manager.get(message.session_id) if message.session_id else None
        if session is None or not session.involves(user_id):
            await _send(websocket, error_message("Sessao invalida", message.session_id))
            return
        if message.type == WSMessageType.CHAT_MESSAGE and session.state != SessionState.ACTIVE:
            await _send(websocket, error_message("Sessao nao esta ativa", session.id))
            return
        session.touch()
        delivered = await send_to_user(session.peer_of(user_id), message)
        if message.type == WSMessageType.CHAT_MESSAGE:
            # Apenas metadados sao registrados — o conteudo e efemero e cifrado.
            log_event(EVENT_MESSAGE_SENT, session_id=session.id, mode=session.mode.value)
            if delivered > 0:
                log_event(EVENT_MESSAGE_RECEIVED, session_id=session.id, mode=session.mode.value)
        return

    await _send(websocket, error_message(f"Tipo nao suportado: {message.type.value}"))
