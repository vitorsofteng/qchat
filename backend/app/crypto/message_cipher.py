"""Cifragem simetrica de mensagens da sessao — AES-256-GCM (F10).

Cada mensagem usa um nonce de 96 bits unico. O associated data (AAD) liga o
ciphertext a `session_id`, `sequence_number` e `timestamp`, protegendo contra
replay e reordenacao. A tag de 128 bits autentica a mensagem.
"""

from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass
from typing import Any

from Crypto.Cipher import AES

KEY_BYTES = 32  # 256 bits
NONCE_BYTES = 12  # 96 bits
TAG_BYTES = 16  # 128 bits


class MessageAuthenticationError(Exception):
    """Falha na verificacao da tag GCM — mensagem adulterada ou chave incorreta."""


class ReplayError(Exception):
    """Mensagem repetida ou fora de ordem (sequence_number nao crescente)."""


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


def _build_aad(session_id: str, sequence_number: int, timestamp: str) -> bytes:
    return f"{session_id}|{sequence_number}|{timestamp}".encode()


@dataclass
class EncryptedEnvelope:
    """Pacote transmitido pelo canal junto ao ciphertext."""

    nonce: str
    ciphertext: str
    tag: str
    sequence_number: int
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "nonce": self.nonce,
            "ciphertext": self.ciphertext,
            "tag": self.tag,
            "sequence_number": self.sequence_number,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EncryptedEnvelope:
        return cls(
            nonce=data["nonce"],
            ciphertext=data["ciphertext"],
            tag=data["tag"],
            sequence_number=int(data["sequence_number"]),
            timestamp=str(data["timestamp"]),
        )


class MessageCipher:
    """Cifrador AES-256-GCM ligado a uma sessao.

    Mantem contadores de sequencia: um crescente para envio e o maior valor
    aceito para recepcao, descartando mensagens repetidas/fora de ordem (F10.5).
    """

    def __init__(self, key: bytes, session_id: str) -> None:
        if len(key) != KEY_BYTES:
            raise ValueError(f"Chave deve ter {KEY_BYTES} bytes, recebeu {len(key)}")
        self._key = key
        self._session_id = session_id
        self._send_sequence = 0
        self._last_received_sequence = -1

    def encrypt(self, plaintext: str, timestamp: str) -> EncryptedEnvelope:
        sequence_number = self._send_sequence
        self._send_sequence += 1

        nonce = secrets.token_bytes(NONCE_BYTES)
        cipher = AES.new(self._key, AES.MODE_GCM, nonce=nonce, mac_len=TAG_BYTES)
        cipher.update(_build_aad(self._session_id, sequence_number, timestamp))
        ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))

        return EncryptedEnvelope(
            nonce=_b64encode(nonce),
            ciphertext=_b64encode(ciphertext),
            tag=_b64encode(tag),
            sequence_number=sequence_number,
            timestamp=timestamp,
        )

    def decrypt(self, envelope: EncryptedEnvelope) -> str:
        if envelope.sequence_number <= self._last_received_sequence:
            raise ReplayError(
                f"sequence_number {envelope.sequence_number} <= "
                f"ultimo aceito {self._last_received_sequence}"
            )

        cipher = AES.new(
            self._key,
            AES.MODE_GCM,
            nonce=_b64decode(envelope.nonce),
            mac_len=TAG_BYTES,
        )
        cipher.update(_build_aad(self._session_id, envelope.sequence_number, envelope.timestamp))
        try:
            plaintext = cipher.decrypt_and_verify(
                _b64decode(envelope.ciphertext), _b64decode(envelope.tag)
            )
        except ValueError as exc:
            raise MessageAuthenticationError("Falha na verificacao da tag GCM") from exc

        self._last_received_sequence = envelope.sequence_number
        return plaintext.decode("utf-8")
