"""Logging estruturado em JSON (F13).

Eventos de ciclo de vida da sessao sao registrados em formato JSON, com
timestamp ISO 8601, em arquivo rotativo (5 MB, 10 arquivos) e em stdout no modo
dev. A atividade de Eve vai para um arquivo separado (F11.5).
"""

from __future__ import annotations

import json
import logging
import logging.handlers
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pythonjsonlogger import jsonlogger

from app.core.config import get_settings

LOG_DIR = Path("logs")
EVENT_LOG = LOG_DIR / "qchat.jsonl"
EVE_LOG = LOG_DIR / "eve.jsonl"

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB por arquivo (F13.4)
_BACKUP_COUNT = 10

# Tipos de evento registrados (F13.2).
EVENT_SESSION_CREATED = "session_created"
EVENT_KEY_ESTABLISHED = "key_established"
EVENT_QBER_MEASURED = "qber_measured"
EVENT_EVE_DETECTED = "eve_detected"
EVENT_MESSAGE_SENT = "message_sent"
EVENT_MESSAGE_RECEIVED = "message_received"
EVENT_SESSION_CLOSED = "session_closed"

_EVENTS_LOGGER = "qchat.events"
_EVE_LOGGER = "qchat.eve"

# Os loggers operam em INFO desde o import; configure_logging() apenas anexa
# os handlers (arquivo/stdout). Assim log_event funciona mesmo sem configuracao.
logging.getLogger(_EVENTS_LOGGER).setLevel(logging.INFO)
logging.getLogger(_EVE_LOGGER).setLevel(logging.INFO)

_configured = False


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def configure_logging() -> None:
    """Configura os loggers. Idempotente — seguro chamar mais de uma vez."""
    global _configured
    if _configured:
        return

    settings = get_settings()
    formatter = jsonlogger.JsonFormatter("%(message)s")

    for logger_name, log_path in ((_EVENTS_LOGGER, EVENT_LOG), (_EVE_LOGGER, EVE_LOG)):
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        logger.handlers.clear()

        # Arquivo rotativo — desativado em testes para nao poluir o disco.
        if settings.environment != "test":
            LOG_DIR.mkdir(exist_ok=True)
            file_handler = logging.handlers.RotatingFileHandler(
                log_path, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # stdout no modo dev (F13.4).
        if not settings.is_production and settings.environment != "test":
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)

    _configured = True


def log_event(
    event: str,
    *,
    session_id: str | None = None,
    mode: str | None = None,
    **fields: Any,
) -> None:
    """Registra um evento estruturado no log de eventos."""
    record = {
        "event": event,
        "timestamp": _utc_now_iso(),
        "session_id": session_id,
        "mode": mode,
        **fields,
    }
    logging.getLogger(_EVENTS_LOGGER).info(event, extra=record)


def log_eve_activity(
    *, mode: str, intercepted: int, qber: float | None, aborted: bool, **fields: Any
) -> None:
    """Registra a atividade do adversario simulado em arquivo separado (F11.5)."""
    record = {
        "event": "eve_activity",
        "timestamp": _utc_now_iso(),
        "eve_mode": mode,
        "intercepted": intercepted,
        "qber": qber,
        "aborted": aborted,
        **fields,
    }
    logging.getLogger(_EVE_LOGGER).info("eve_activity", extra=record)


def read_events(session_id: str | None = None, log_dir: Path = LOG_DIR) -> list[dict[str, Any]]:
    """Le os eventos dos arquivos de log, opcionalmente filtrados por session_id."""
    events: list[dict[str, Any]] = []
    for path in sorted(log_dir.glob("qchat.jsonl*")):
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if session_id is None or record.get("session_id") == session_id:
                events.append(record)
    return events
