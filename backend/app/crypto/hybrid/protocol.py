"""Combinador hibrido BB84 + ML-KEM (F8).

Executa os dois protocolos componentes e combina as chaves via HKDF. A chave
hibrida e segura enquanto ao menos um componente permanecer seguro: se um deles
falhar, o protocolo registra o evento e continua com o sobrevivente (F8.5).
"""

from __future__ import annotations

import base64
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from app.crypto.bb84.protocol import BB84Protocol
from app.crypto.hybrid.combiner import combine_keys, generate_salt
from app.crypto.key_protocol import (
    KeyEstablishmentProtocol,
    ProtocolMetrics,
    ProtocolMode,
    run_exchange,
)
from app.crypto.mlkem.protocol import MLKEMProtocol


class HybridComponentsFailedError(Exception):
    """Ambos os componentes falharam — nao ha chave sobrevivente para o hibrido."""


@dataclass
class _ComponentOutcome:
    name: str
    ok: bool
    key: bytes | None = None
    qber: float | None = None
    error: str | None = None


def _run_component(name: str, factory: Callable[[], KeyEstablishmentProtocol]) -> _ComponentOutcome:
    """Executa a troca completa de um componente, capturando qualquer falha (F8.5)."""
    try:
        initiator = factory()
        key, _ = run_exchange(initiator, factory())
    except Exception as exc:  # qualquer falha do componente e tolerada pelo hibrido
        return _ComponentOutcome(
            name=name, ok=False, error=str(exc), qber=getattr(exc, "qber", None)
        )
    return _ComponentOutcome(name=name, ok=True, key=key, qber=initiator.get_metrics().qber)


class HybridProtocol(KeyEstablishmentProtocol):
    mode = ProtocolMode.HYBRID

    def __init__(self) -> None:
        self._key: bytes | None = None
        self._salt: bytes | None = None
        self._qber: float | None = None
        self._elapsed_ms = 0.0
        self._survivors: list[str] = []
        self._report: dict[str, Any] = {}

    def initiate(self) -> dict[str, Any]:
        start = time.perf_counter()
        # BB84 e ML-KEM executam em paralelo (F8.4). A interface e sincrona,
        # entao usa-se um ThreadPoolExecutor — qiskit e liboqs liberam o GIL.
        with ThreadPoolExecutor(max_workers=2) as executor:
            bb84_future = executor.submit(_run_component, "bb84", BB84Protocol)
            mlkem_future = executor.submit(_run_component, "mlkem", MLKEMProtocol)
            bb84 = bb84_future.result()
            mlkem = mlkem_future.result()

        component_keys: list[bytes] = []
        for outcome in (bb84, mlkem):  # ordem fixa: ikm = K_bb84 || K_mlkem (F8.2)
            self._report[outcome.name] = {"ok": outcome.ok, "error": outcome.error}
            if outcome.ok and outcome.key is not None:
                self._survivors.append(outcome.name)
                component_keys.append(outcome.key)

        self._qber = bb84.qber

        if not component_keys:
            raise HybridComponentsFailedError(f"BB84: {bb84.error}; ML-KEM: {mlkem.error}")

        self._salt = generate_salt()
        self._key = combine_keys(component_keys, self._salt)
        self._elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "key": base64.b64encode(self._key).decode("ascii"),
            "salt": base64.b64encode(self._salt).decode("ascii"),
            "survivors": list(self._survivors),
            "report": self._report,
        }

    def respond(self, initiation_data: dict[str, Any]) -> dict[str, Any]:
        self._key = base64.b64decode(initiation_data["key"])
        self._salt = base64.b64decode(initiation_data["salt"])
        self._survivors = list(initiation_data.get("survivors", []))
        self._report = initiation_data.get("report", {})
        return {}

    def get_key(self) -> bytes:
        if self._key is None:
            raise RuntimeError("Chave de sessao ainda nao estabelecida")
        return self._key

    def get_metrics(self) -> ProtocolMetrics:
        return ProtocolMetrics(
            mode=self.mode,
            elapsed_ms=self._elapsed_ms,
            qber=self._qber,
            bytes_exchanged=0,
            key_size_bits=len(self._key) * 8 if self._key else 0,
            extra={"survivors": list(self._survivors), "components": self._report},
        )
