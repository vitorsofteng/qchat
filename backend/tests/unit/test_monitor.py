"""Testes do monitor de QBER e dos observers — padrao Observer (F12)."""

import logging

from app.core.session_manager import Session, SessionManager, SessionState
from app.crypto.key_protocol import ProtocolMode
from app.monitor.observers import Logger, NotificationService, Observer, SessionTerminator
from app.monitor.qber_monitor import QBERMonitor
from app.schemas.ws import WSMessageType


class _RecordingObserver(Observer):
    def __init__(self) -> None:
        self.events: list[dict] = []

    def on_event(self, event: dict) -> None:
        self.events.append(event)


def _make_session(mode: ProtocolMode = ProtocolMode.BB84) -> Session:
    return Session(id="sess-test", alice_id="alice-id", bob_id="bob-id", mode=mode)


# --------------------------------------------------------------------- QBERMonitor
def test_monitor_notifies_observer_below_threshold():
    monitor = QBERMonitor(threshold=0.15)
    observer = _RecordingObserver()
    monitor.attach(observer)
    exceeded = monitor.update_qber(0.05, "sess-1")
    assert exceeded is False
    assert [e["type"] for e in observer.events] == ["qber_measured"]


def test_monitor_emits_eve_detected_above_threshold():
    monitor = QBERMonitor(threshold=0.15)
    observer = _RecordingObserver()
    monitor.attach(observer)
    exceeded = monitor.update_qber(0.25, "sess-1")
    assert exceeded is True
    assert [e["type"] for e in observer.events] == ["qber_measured", "eve_detected"]


def test_monitor_detach_stops_notifications():
    monitor = QBERMonitor(threshold=0.15)
    observer = _RecordingObserver()
    monitor.attach(observer)
    monitor.detach(observer)
    monitor.update_qber(0.25, "sess-1")
    assert observer.events == []


# --------------------------------------------------------------- NotificationService
def test_notification_service_alerts_only_when_exceeded():
    session = _make_session()
    notifier = NotificationService(session)
    monitor = QBERMonitor(threshold=0.15)
    monitor.attach(notifier)

    monitor.update_qber(0.05, session.id)
    assert notifier.drain() == []

    monitor.update_qber(0.30, session.id)
    pending = notifier.drain()
    assert len(pending) == 2  # alerta para Alice e Bob
    assert all(message.type == WSMessageType.QBER_ALERT for _, message in pending)
    assert notifier.drain() == []  # drain esvazia a fila


# ---------------------------------------------------------------- SessionTerminator
def test_session_terminator_closes_session_on_eve():
    manager = SessionManager()
    session = manager.create_session("alice-term", "bob-term", ProtocolMode.BB84)
    monitor = QBERMonitor(threshold=0.15)
    monitor.attach(SessionTerminator(manager))
    monitor.update_qber(0.40, session.id)
    assert manager.get(session.id).state == SessionState.ABORTED


def test_session_terminator_ignores_normal_qber():
    manager = SessionManager()
    session = manager.create_session("alice-ok", "bob-ok", ProtocolMode.BB84)
    monitor = QBERMonitor(threshold=0.15)
    monitor.attach(SessionTerminator(manager))
    monitor.update_qber(0.05, session.id)
    assert manager.get(session.id).state != SessionState.ABORTED


# ------------------------------------------------------------------------- Logger
def test_logger_observer_emits_structured_events():
    captured: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record)

    events_logger = logging.getLogger("qchat.events")
    handler = _Capture()
    events_logger.addHandler(handler)
    try:
        monitor = QBERMonitor(threshold=0.15)
        monitor.attach(Logger(mode="BB84"))
        monitor.update_qber(0.25, "sess-log")
    finally:
        events_logger.removeHandler(handler)

    messages = [record.getMessage() for record in captured]
    assert "qber_measured" in messages
    assert "eve_detected" in messages
