"""Envio de mensagens atraves do pool de conexoes WebSocket."""

from app.core.session_manager import SessionManager
from app.schemas.ws import WSMessage


async def send_to_user(user_id: str, message: WSMessage) -> int:
    """Entrega a mensagem a todas as conexoes ativas do usuario.

    Retorna o numero de conexoes que receberam. Envio e best-effort: conexoes
    mortas sao ignoradas e limpas pelo proprio handler do WebSocket.
    """
    manager = SessionManager()
    data = message.model_dump(mode="json")
    delivered = 0
    for websocket in manager.connections_for(user_id):
        try:
            await websocket.send_json(data)
            delivered += 1
        except (RuntimeError, ConnectionError):
            pass
    return delivered
