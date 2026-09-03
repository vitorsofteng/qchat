"""Combinador hibrido — HKDF-SHA256 conforme RFC 5869 (F8.1).

K_final = HKDF(salt = nonce aleatorio de 32B, ikm = K_bb84 || K_mlkem,
               info = "qchat-hybrid-v1", length = 32).

A chave hibrida permanece segura enquanto pelo menos um dos componentes
permanecer seguro.
"""

from __future__ import annotations

import secrets

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

HYBRID_INFO = b"qchat-hybrid-v1"
SALT_BYTES = 32
COMBINED_KEY_BYTES = 32


def generate_salt() -> bytes:
    """Salt aleatorio de 32 bytes, trocado entre Alice e Bob (F8.3)."""
    return secrets.token_bytes(SALT_BYTES)


def combine_keys(component_keys: list[bytes], salt: bytes) -> bytes:
    """Deriva a chave hibrida final via HKDF-SHA256.

    Com ambos os componentes, ``ikm = K_bb84 || K_mlkem`` (F8.2). Com apenas um
    componente sobrevivente, ``ikm`` e a chave desse componente (F8.5).
    """
    if not component_keys:
        raise ValueError("E necessario ao menos uma chave componente")
    if len(salt) != SALT_BYTES:
        raise ValueError(f"Salt deve ter {SALT_BYTES} bytes, recebeu {len(salt)}")

    ikm = b"".join(component_keys)
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=COMBINED_KEY_BYTES,
        salt=salt,
        info=HYBRID_INFO,
    )
    return hkdf.derive(ikm)
