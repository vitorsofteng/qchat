"""Protocolo RSA — controle experimental (F9).

Fluxo:
  initiate()  -> iniciador gera par RSA-2048 e envia a chave publica
  respond()   -> respondente gera chave de sessao de 32B, cifra com RSA-OAEP
  finalize()  -> iniciador decifra o ciphertext e recupera a chave
"""

from __future__ import annotations

import base64
import secrets
import time
from typing import Any

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

from app.crypto.key_protocol import (
    SESSION_KEY_BYTES,
    KeyEstablishmentProtocol,
    ProtocolMetrics,
    ProtocolMode,
)

RSA_KEY_BITS = 2048


def _b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _b64decode(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))


class RSAProtocol(KeyEstablishmentProtocol):
    mode = ProtocolMode.RSA

    def __init__(self) -> None:
        self._rsa_key: RSA.RsaKey | None = None  # iniciador: par completo (pub + priv)
        self._session_key: bytes | None = None
        self._elapsed_ms: float = 0.0
        self._bytes_exchanged: int = 0

    def initiate(self) -> dict[str, Any]:
        start = time.perf_counter()
        self._rsa_key = RSA.generate(RSA_KEY_BITS)
        public_pem = self._rsa_key.publickey().export_key()
        self._bytes_exchanged += len(public_pem)
        self._elapsed_ms += (time.perf_counter() - start) * 1000
        return {"public_key": public_pem.decode("ascii")}

    def respond(self, initiation_data: dict[str, Any]) -> dict[str, Any]:
        start = time.perf_counter()
        public_key = RSA.import_key(initiation_data["public_key"].encode("ascii"))
        self._session_key = secrets.token_bytes(SESSION_KEY_BYTES)
        cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
        ciphertext = cipher.encrypt(self._session_key)
        self._bytes_exchanged += len(ciphertext)
        self._elapsed_ms += (time.perf_counter() - start) * 1000
        return {"ciphertext": _b64encode(ciphertext)}

    def finalize(self, response_data: dict[str, Any]) -> None:
        if self._rsa_key is None:
            raise RuntimeError("finalize() chamado antes de initiate()")
        start = time.perf_counter()
        ciphertext = _b64decode(response_data["ciphertext"])
        cipher = PKCS1_OAEP.new(self._rsa_key, hashAlgo=SHA256)
        # decrypt() lanca ValueError se o ciphertext for invalido -> aborta a sessao.
        self._session_key = cipher.decrypt(ciphertext)
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
            extra={"rsa_key_bits": RSA_KEY_BITS},
        )
