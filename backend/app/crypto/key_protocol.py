"""Interface comum dos protocolos de estabelecimento de chave (F5).

Todos os modos (BB84, ML-KEM, Hibrido, RSA) implementam este contrato. Cada
instancia representa **um participante** da troca. A troca completa em processo
(usada por testes e pelos scripts de experimento) e feita por `run_exchange`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Tamanho da chave de sessao final, em bytes (256 bits para AES-256-GCM).
SESSION_KEY_BYTES = 32


class ProtocolMode(str, Enum):
    BB84 = "BB84"
    MLKEM = "MLKEM"
    HYBRID = "HYBRID"
    RSA = "RSA"


@dataclass
class ProtocolMetrics:
    """Metricas coletadas durante a execucao de um protocolo."""

    mode: ProtocolMode
    elapsed_ms: float = 0.0
    qber: float | None = None
    bytes_exchanged: int = 0
    key_size_bits: int = 0
    extra: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "elapsed_ms": round(self.elapsed_ms, 3),
            "qber": self.qber,
            "bytes_exchanged": self.bytes_exchanged,
            "key_size_bits": self.key_size_bits,
            **self.extra,
        }


class KeyEstablishmentProtocol(ABC):
    """Contrato comum aos quatro modos de estabelecimento de chave.

    Fluxo em tres fases (cobre RSA e ML-KEM; BB84/Hibrido estendem):
      1. iniciador  -> ``initiate()``            produz a primeira mensagem
      2. respondente -> ``respond(msg1)``        consome msg1, produz msg2
      3. iniciador  -> ``finalize(msg2)``        consome msg2, deriva a chave
    """

    mode: ProtocolMode

    @abstractmethod
    def initiate(self) -> dict[str, Any]:
        """Iniciador gera a primeira mensagem do protocolo."""

    @abstractmethod
    def respond(self, initiation_data: dict[str, Any]) -> dict[str, Any]:
        """Respondente processa a iniciacao e produz a resposta."""

    def finalize(self, response_data: dict[str, Any]) -> None:  # noqa: B027
        """Etapa final opcional do iniciador. Protocolos de duas mensagens nao usam."""

    @abstractmethod
    def get_key(self) -> bytes:
        """Retorna a chave de sessao de 32 bytes estabelecida."""

    @abstractmethod
    def get_metrics(self) -> ProtocolMetrics:
        """Retorna as metricas coletadas durante a execucao."""


def run_exchange(
    initiator: KeyEstablishmentProtocol,
    responder: KeyEstablishmentProtocol,
) -> tuple[bytes, bytes]:
    """Executa a troca completa em processo entre duas instancias do mesmo modo.

    Retorna ``(chave_iniciador, chave_respondente)`` — iguais quando o protocolo
    e bem-sucedido. Util para testes unitarios e scripts de experimento.
    """
    msg1 = initiator.initiate()
    msg2 = responder.respond(msg1)
    initiator.finalize(msg2)
    return initiator.get_key(), responder.get_key()
