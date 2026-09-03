"""Testes unitarios do protocolo ML-KEM (F16.2).

Pulados quando o extra `pqc` (liboqs-python) nao esta instalado.
"""

import base64

import pytest

pytest.importorskip("oqs", reason="extra 'pqc' (liboqs-python) nao instalado")

from app.crypto.key_protocol import ProtocolMode, run_exchange  # noqa: E402
from app.crypto.mlkem.protocol import MLKEMDecapsulationError, MLKEMProtocol  # noqa: E402


def test_exchange_produces_equal_32_byte_keys():
    initiator, responder = MLKEMProtocol(), MLKEMProtocol()
    key_a, key_b = run_exchange(initiator, responder)
    assert key_a == key_b
    assert len(key_a) == 32


def test_keys_random_across_runs():
    key1, _ = run_exchange(MLKEMProtocol(), MLKEMProtocol())
    key2, _ = run_exchange(MLKEMProtocol(), MLKEMProtocol())
    assert key1 != key2


def test_mlkem_768_message_sizes():
    # F7.6: pk = 1184 B, ct = 1088 B, K = 32 B para ML-KEM-768.
    initiator, responder = MLKEMProtocol("ML-KEM-768"), MLKEMProtocol("ML-KEM-768")
    msg1 = initiator.initiate()
    assert len(base64.b64decode(msg1["public_key"])) == 1184
    msg2 = responder.respond(msg1)
    assert len(base64.b64decode(msg2["ciphertext"])) == 1088
    initiator.finalize(msg2)
    assert len(initiator.get_key()) == 32


def test_metrics_after_exchange():
    initiator, responder = MLKEMProtocol(), MLKEMProtocol()
    run_exchange(initiator, responder)
    metrics = initiator.get_metrics()
    assert metrics.mode == ProtocolMode.MLKEM
    assert metrics.key_size_bits == 256
    assert metrics.qber is None
    assert metrics.elapsed_ms > 0
    assert metrics.extra["mlkem_level"] == "ML-KEM-768"


def test_unsupported_level_rejected():
    with pytest.raises(ValueError):
        MLKEMProtocol("ML-KEM-999")


def test_get_key_before_exchange_raises():
    with pytest.raises(RuntimeError):
        MLKEMProtocol().get_key()


def test_finalize_before_initiate_raises():
    with pytest.raises(RuntimeError):
        MLKEMProtocol().finalize({"ciphertext": "AA=="})


def test_malformed_ciphertext_rejected():
    initiator = MLKEMProtocol("ML-KEM-768")
    initiator.initiate()
    with pytest.raises(ValueError):
        initiator.finalize({"ciphertext": base64.b64encode(b"curto").decode("ascii")})


def test_tampered_ciphertext_yields_different_key():
    # ML-KEM tem rejeicao implicita: ct adulterado produz K diferente, sem erro.
    initiator = MLKEMProtocol("ML-KEM-768")
    responder = MLKEMProtocol("ML-KEM-768")
    msg1 = initiator.initiate()
    msg2 = responder.respond(msg1)

    ciphertext = bytearray(base64.b64decode(msg2["ciphertext"]))
    ciphertext[0] ^= 0xFF
    initiator.finalize({"ciphertext": base64.b64encode(bytes(ciphertext)).decode("ascii")})

    assert initiator.get_key() != responder.get_key()


def test_decapsulation_error_is_available():
    # MLKEMDecapsulationError envolve falhas vindas do liboqs.
    assert issubclass(MLKEMDecapsulationError, Exception)
