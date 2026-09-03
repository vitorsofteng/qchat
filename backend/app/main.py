"""QChat — entry point da aplicacao FastAPI."""

import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import auth, logs, session, users, websocket
from app.core.config import get_settings
from app.core.database import init_db
from app.core.event_logging import EVENT_SESSION_CLOSED, configure_logging, log_event
from app.core.session_manager import SessionManager

settings = get_settings()

_CLEANUP_INTERVAL_SECONDS = 60


async def _session_cleanup_loop() -> None:
    """Encerra periodicamente sessoes inativas alem do timeout (F3.7)."""
    manager = SessionManager()
    while True:
        await asyncio.sleep(_CLEANUP_INTERVAL_SECONDS)
        for session_id in manager.cleanup_expired(settings.session_timeout_minutes):
            closed = manager.get(session_id)
            log_event(
                EVENT_SESSION_CLOSED,
                session_id=session_id,
                mode=closed.mode.value if closed else None,
                reason="timeout",
            )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    init_db()
    cleanup_task = asyncio.create_task(_session_cleanup_loop())
    yield
    cleanup_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await cleanup_task


app = FastAPI(
    title="QChat API",
    description="Sistema de chat hibrido QKD+PQC — TCC",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(session.router)
app.include_router(websocket.router)
app.include_router(logs.router)
app.include_router(users.router)


@app.get("/health", tags=["infra"])
def health() -> dict:
    """Health check para orquestracao e monitoramento."""
    return {"status": "ok", "app": settings.app_name, "version": __version__}


@app.get("/config", tags=["infra"])
def public_config() -> dict:
    """Parametros publicos do sistema, exibidos no frontend (somente leitura)."""
    return {
        "bb84_qubits": settings.bb84_qubits,
        "qber_threshold": settings.qber_threshold,
        "cascade_passes": settings.cascade_passes,
        "mlkem_level": settings.mlkem_level,
        "session_timeout_minutes": settings.session_timeout_minutes,
    }
