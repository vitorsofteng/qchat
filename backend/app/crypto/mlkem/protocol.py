"""Protocolo ML-KEM — encapsulamento de chave pos-quantico, NIST FIPS 203 (F7).

Usa liboqs-python (implementacao de referencia Open Quantum Safe). Fluxo:
  initiate()  -> iniciador (Bob) gera (pk, sk) e envia pk
  respond()   -> respondente (Alice) encapsula -> (ct, K), envia ct
  finalize()  -> iniciador decapsula ct com sk -> recupera K
"""

from __future__ import annotations

import base64
import time
from typing import TYPE_CHECKING, Any

from app.core.config import get_settings
from app.crypto.key_protocol import (
    KeyEstablishmentProtocol,
    ProtocolMetrics,
    ProtocolMode,
)

if TYPE_CHECKING:
    import oqs

# Tamanhos esperados (bytes) por nivel de seguranca ML-KEM, conforme FIPS 203 (F7.6).
_EXPECTED_SIZES: dict[str, dict[str, int]] = {
    "ML-KEM-512": {"public_key": 800, "ciphertext": 768, "shared_secret": 32},
    "ML-KEM-768": {"public_key": 1184, "ciphertext": 1088, "shared_secret": 32},
    "ML-KEM-1024": {"public_key": 1568, "ciphertext": 1568, "shared_secret": 32},
}


class MLKEMDecapsulationError(Exception):
    """Falha no decapsulamento ML-KEM — ciphertext malformado ou invalido (F7.7)."""


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


class MLKEMProtocol(KeyEstablishmentProtocol):
    mode = ProtocolMode.MLKEM

    def __init__(self, level: str | None = None) -> None:
        self._level = level or get_settings().mlkem_level
        if self._level not in _EXPECTED_SIZES:
            raise ValueError(
                f"Nivel ML-KEM nao suportado: {self._level}. "
                f"Disponiveis: {sorted(_EXPECTED_SIZES)}"
            )
        self._kem: oqs.KeyEncapsulation | None = None  # iniciador: detem a chave secreta
        self._session_key: bytes | None = None
        self._elapsed_ms: float = 0.0
        self._bytes_exchanged: int = 0

    def initiate(self) -> dict[str, Any]:
        import oqs

        start = time.perf_counter()
        self._kem = oqs.KeyEncapsulation(self._level)
        public_key = self._kem.generate_keypair()
        self._validate_size("public_key", public_key)
        self._bytes_exchanged += len(public_key)
        self._elapsed_ms += (time.perf_counter() - start) * 1000
        return {"public_key": _b64encode(public_key)}

    def respond(self, initiation_data: dict[str, Any]) -> dict[str, Any]:
        import oqs

        start = time.perf_counter()
        public_key = _b64decode(initiation_data["public_key"])
        self._validate_size("public_key", public_key)
        with oqs.KeyEncapsulation(self._level) as kem:
            ciphertext, shared_secret = kem.encap_secret(public_key)
        self._validate_size("ciphertext", ciphertext)
        self._validate_size("shared_secret", shared_secret)
        self._session_key = bytes(shared_secret)
        self._bytes_exchanged += len(ciphertext)
        self._elapsed_ms += (time.perf_counter() - start) * 1000
        return {"ciphertext": _b64encode(ciphertext)}

    def finalize(self, response_data: dict[str, Any]) -> None:
        if self._kem is None:
            raise RuntimeError("finalize() chamado antes de initiate()")
        start = time.perf_counter()
        ciphertext = _b64decode(response_data["ciphertext"])
        self._validate_size("ciphertext", ciphertext)
        try:
            shared_secret = self._kem.decap_secret(ciphertext)
        except Exception as exc:  # liboqs sinaliza ciphertext invalido via RuntimeError
            raise MLKEMDecapsulationError(str(exc)) from exc
        finally:
            self._kem.free()
            self._kem = None
        self._session_key = bytes(shared_secret)
        self._elapsed_ms += (time.perf_counter() - start) * 1000

    def get_key(self) -> bytes:
        if self._session_key is None:
            raise RuntimeError("Chave de sessao ainda nao estabelecida")
        return self._session_key

    def get_metrics(self) -> ProtocolMetrics:
        return ProtocolMetrics(
            mode=self.mode,
            elapsed_ms=self._elapsed_ms,
            qber=None,
            bytes_exchanged=self._bytes_exchanged,
            key_size_bits=len(self._session_key) * 8 if self._session_key else 0,
            extra={"mlkem_level": self._level},
        )

    def _validate_size(self, kind: str, data: bytes) -> None:
        expected = _EXPECTED_SIZES[self._level][kind]
        if len(data) != expected:
            raise ValueError(f"{kind} de {self._level} tem {len(data)} bytes, esperado {expected}")
