"""Testes unitarios da cifragem AES-256-GCM (F16.4)."""

import pytest

from app.crypto.message_cipher import (
    EncryptedEnvelope,
    MessageAuthenticationError,
    MessageCipher,
    ReplayError,
)

KEY = bytes(range(32))
TIMESTAMP = "2026-05-21T12:00:00Z"


def test_encrypt_decrypt_roundtrip():
    sender = MessageCipher(KEY, "sess-1")
    receiver = MessageCipher(KEY, "sess-1")
    envelope = sender.encrypt("ola, mundo quantico", TIMESTAMP)
    assert receiver.decrypt(envelope) == "ola, mundo quantico"


def test_wrong_key_fails_tag_verification():
    sender = MessageCipher(KEY, "sess-1")
    receiver = MessageCipher(bytes(32), "sess-1")
    envelope = sender.encrypt("segredo", TIMESTAMP)
    with pytest.raises(MessageAuthenticationError):
        receiver.decrypt(envelope)


def test_aad_mismatch_detected():
    # session_id diferente -> AAD diverge -> falha de autenticacao (F10.3).
    sender = MessageCipher(KEY, "sess-A")
    receiver = MessageCipher(KEY, "sess-B")
    envelope = sender.encrypt("x", TIMESTAMP)
    with pytest.raises(MessageAuthenticationError):
        receiver.decrypt(envelope)


def test_tampered_ciphertext_detected():
    sender = MessageCipher(KEY, "sess-1")
    receiver = MessageCipher(KEY, "sess-1")
    envelope = sender.encrypt("conteudo", TIMESTAMP)
    corrupted = envelope.to_dict()
    corrupted["tag"] = "A" * len(corrupted["tag"])
    with pytest.raises(MessageAuthenticationError):
        receiver.decrypt(EncryptedEnvelope.from_dict(corrupted))


def test_replayed_message_rejected():
    sender = MessageCipher(KEY, "sess-1")
    receiver = MessageCipher(KEY, "sess-1")
    envelope = sender.encrypt("uma vez", TIMESTAMP)
    receiver.decrypt(envelope)
    with pytest.raises(ReplayError):
        receiver.decrypt(envelope)


def test_sequence_numbers_are_incremental():
    sender = MessageCipher(KEY, "sess-1")
    first = sender.encrypt("a", TIMESTAMP)
    second = sender.encrypt("b", TIMESTAMP)
    assert first.sequence_number == 0
    assert second.sequence_number == 1


def test_invalid_key_length_rejected():
    with pytest.raises(ValueError):
        MessageCipher(b"curta-demais", "sess-1")
