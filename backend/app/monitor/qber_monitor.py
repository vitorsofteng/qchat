"""Monitor de QBER — Subject do padrao Observer (F12.1).

Recebe medicoes de QBER e notifica os observers registrados. Quando o valor
ultrapassa o limiar, emite tambem um evento `eve_detected`.
"""

from __future__ import annotations

from typing import Any

from app.core.event_logging import EVENT_EVE_DETECTED, EVENT_QBER_MEASURED
from app.monitor.observers import Observer


class QBERMonitor:
    def __init__(self, threshold: float) -> None:
        self.threshold = threshold
        self._observers: list[Observer] = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def update_qber(self, value: float, session_id: str) -> bool:
        """Registra uma medicao de QBER e notifica os observers.

        Retorna ``True`` se o valor ultrapassou o limiar.
        """
        exceeded = value > self.threshold
        base: dict[str, Any] = {
            "session_id": session_id,
            "qber": value,
            "threshold": self.threshold,
            "exceeded": exceeded,
        }
        self._notify({**base, "type": EVENT_QBER_MEASURED})
        if exceeded:
            self._notify({**base, "type": EVENT_EVE_DETECTED})
        return exceeded

    def _notify(self, event: dict[str, Any]) -> None:
        for observer in self._observers:
            observer.on_event(event)
