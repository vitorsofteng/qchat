"""Testes unitarios do protocolo RSA (F16.5)."""

import pytest

from app.crypto.key_protocol import ProtocolMode, run_exchange
from app.crypto.rsa.protocol import RSAProtocol


def test_exchange_produces_equal_32_byte_keys():
    initiator, responder = RSAProtocol(), RSAProtocol()
    key_a, key_b = run_exchange(initiator, responder)
    assert key_a == key_b
    assert len(key_a) == 32


def test_exchange_keys_are_random_across_runs():
    key1, _ = run_exchange(RSAProtocol(), RSAProtocol())
    key2, _ = run_exchange(RSAProtocol(), RSAProtocol())
    assert key1 != key2


def test_metrics_after_exchange():
    initiator, responder = RSAProtocol(), RSAProtocol()
    run_exchange(initiator, responder)
    metrics = initiator.get_metrics()
    assert metrics.mode == ProtocolMode.RSA
    assert metrics.key_size_bits == 256
    assert metrics.qber is None
    assert metrics.elapsed_ms > 0
    assert metrics.bytes_exchanged > 0


def test_get_key_before_exchange_raises():
    with pytest.raises(RuntimeError):
        RSAProtocol().get_key()


def test_finalize_before_initiate_raises():
    with pytest.raises(RuntimeError):
        RSAProtocol().finalize({"ciphertext": "AA=="})
