"""Orquestracao do estabelecimento de chave de uma sessao.

Decisao de arquitetura: o **servidor** executa o protocolo de estabelecimento
de chave (modulos `crypto/`) e distribui a chave resultante aos dois
participantes pelo canal WSS. Isso mantem os modulos criptograficos — objeto
de estudo do TCC — como a implementacao de referencia, e o frontend cifra/
decifra as mensagens com a mesma chave (Web Crypto). O canal WSS/TLS protege a
chave em transito; o modelo de ameacas do TCC exclui comprometimento de
servidor/endpoint durante a sessao.
"""

from __future__ import annotations

import base64

from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.event_logging import EVENT_KEY_ESTABLISHED, EVENT_SESSION_CLOSED, log_event
from app.core.session_manager import Session, SessionManager
from app.crypto.bb84.protocol import QBERThresholdExceeded
from app.crypto.key_protocol import KeyEstablishmentProtocol, ProtocolMode, run_exchange
from app.crypto.protocol_factory import ProtocolFactory
from app.monitor.observers import Logger, NotificationService, SessionTerminator
from app.monitor.qber_monitor import QBERMonitor
from app.schemas.ws import WSMessage, WSMessageType


def _run_protocol(session: Session) -> tuple[bytes, KeyEstablishmentProtocol]:
    initiator = ProtocolFactory.create(session.mode)
    responder = ProtocolFactory.create(session.mode)
    key_initiator, key_responder = run_exchange(initiator, responder)
    if key_initiator != key_responder:
        raise ValueError("Chaves divergentes entre as duas partes")
    return key_initiator, initiator


def _build_qber_monitor(
    session: Session, manager: SessionManager
) -> tuple[QBERMonitor, NotificationService]:
    """Monta o monitor de QBER com seus observers (F12).

    O `SessionTerminator` e anexado apenas para BB84 puro: no modo Hibrido um
    QBER alto compromete somente o componente BB84, mas a chave hibrida
    permanece segura via ML-KEM — a sessao nao deve ser encerrada.
    """
    monitor = QBERMonitor(get_settings().qber_threshold)
    monitor.attach(Logger(mode=session.mode.value))
    notifier = NotificationService(session)
    monitor.attach(notifier)
    if session.mode == ProtocolMode.BB84:
        monitor.attach(SessionTerminator(manager))
    return monitor, notifier


async def establish_session_key(session: Session, manager: SessionManager) -> None:
    """Executa o protocolo da sessao e notifica ambos os participantes.

    Em caso de falha (QBER acima do limiar, extras ausentes, etc.) a sessao e
    encerrada e os participantes sao avisados.
    """
    # Importacao tardia evita ciclo: notifications -> session_manager -> ...
    from app.api.notifications import send_to_user

    monitor, notifier = _build_qber_monitor(session, manager)

    try:
        key, protocol = await run_in_threadpool(_run_protocol, session)
    except QBERThresholdExceeded as exc:
        # BB84 detectou espionagem: o monitor registra, alerta e encerra (F12).
        monitor.update_qber(exc.qber, session.id)
        for user_id, message in notifier.drain():
            await send_to_user(user_id, message)
        return
    except Exception as exc:  # noqa: BLE001 -- qualquer outra falha encerra a sessao
        manager.close_session(session.id, reason="key_exchange_failed")
        log_event(
            EVENT_SESSION_CLOSED,
            session_id=session.id,
            mode=session.mode.value,
            reason="key_exchange_failed",
        )
        error = WSMessage(
            type=WSMessageType.ERROR,
            session_id=session.id,
            payload={"detail": f"Falha no estabelecimento de chave: {exc}"},
        )
        await send_to_user(session.alice_id, error)
        await send_to_user(session.bob_id, error)
        return

    metrics = protocol.get_metrics()

    # QBER medido (BB84/Hibrido): o monitor registra e, se exceder, alerta.
    if metrics.qber is not None:
        monitor.update_qber(metrics.qber, session.id)
        for user_id, message in notifier.drain():
            await send_to_user(user_id, message)

    manager.set_key(session.id, key, qber=metrics.qber)
    log_event(EVENT_KEY_ESTABLISHED, session_id=session.id, **metrics.as_dict())

    established = WSMessage(
        type=WSMessageType.KEY_ESTABLISHED,
        session_id=session.id,
        payload={
            "key": base64.b64encode(key).decode("ascii"),
            "metrics": metrics.as_dict(),
        },
    )
    await send_to_user(session.alice_id, established)
    await send_to_user(session.bob_id, established)
