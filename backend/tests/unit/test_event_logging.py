"""Testes do logging estruturado de eventos (F13)."""

import json
import logging

from app.core.event_logging import (
    EVENT_KEY_ESTABLISHED,
    log_eve_activity,
    log_event,
    read_events,
)


class _Capture(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def _capture(logger_name: str) -> _Capture:
    handler = _Capture()
    logging.getLogger(logger_name).addHandler(handler)
    return handler


# ----------------------------------------------------------------- read_events
def test_read_events_filters_by_session(tmp_path):
    (tmp_path / "qchat.jsonl").write_text(
        json.dumps({"event": "session_created", "session_id": "s1"})
        + "\n"
        + json.dumps({"event": "key_established", "session_id": "s2"})
        + "\n"
        + json.dumps({"event": "session_closed", "session_id": "s1"})
        + "\n",
        encoding="utf-8",
    )
    events = read_events(session_id="s1", log_dir=tmp_path)
    assert len(events) == 2
    assert all(event["session_id"] == "s1" for event in events)


def test_read_events_returns_all_without_filter(tmp_path):
    (tmp_path / "qchat.jsonl").write_text(
        json.dumps({"event": "x", "session_id": "s1"}) + "\n", encoding="utf-8"
    )
    assert len(read_events(log_dir=tmp_path)) == 1


def test_read_events_missing_directory(tmp_path):
    assert read_events(session_id="any", log_dir=tmp_path / "nao-existe") == []


def test_read_events_skips_malformed_lines(tmp_path):
    (tmp_path / "qchat.jsonl").write_text(
        "linha invalida\n" + json.dumps({"event": "ok", "session_id": "s"}) + "\n",
        encoding="utf-8",
    )
    assert len(read_events(log_dir=tmp_path)) == 1


# ------------------------------------------------------------------- log_event
def test_log_event_emits_structured_record():
    handler = _capture("qchat.events")
    try:
        log_event(EVENT_KEY_ESTABLISHED, session_id="s1", mode="RSA", elapsed_ms=12.0)
    finally:
        logging.getLogger("qchat.events").removeHandler(handler)

    assert len(handler.records) == 1
    record = handler.records[0]
    assert record.getMessage() == "key_established"
    assert record.session_id == "s1"
    assert record.mode == "RSA"


def test_log_eve_activity_uses_separate_logger():
    handler = _capture("qchat.eve")
    try:
        log_eve_activity(mode="INTERCEPT_RESEND", intercepted=100, qber=0.25, aborted=True)
    finally:
        logging.getLogger("qchat.eve").removeHandler(handler)

    assert len(handler.records) == 1
    record = handler.records[0]
    assert record.eve_mode == "INTERCEPT_RESEND"
    assert record.intercepted == 100
    assert record.aborted is True
