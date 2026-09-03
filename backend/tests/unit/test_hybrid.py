"""Testes do combinador hibrido BB84 + ML-KEM (F16.3).

Pulados quando os extras `pqc` e `qkd` nao estao instalados.
"""

import pytest

pytest.importorskip("oqs", reason="extra 'pqc' (liboqs-python) nao instalado")
pytest.importorskip("qiskit_aer", reason="extra 'qkd' (qiskit) nao instalado")

from app.crypto.hybrid.combiner import (  # noqa: E402
    COMBINED_KEY_BYTES,
    combine_keys,
    generate_salt,
)
from app.crypto.hybrid.protocol import (  # noqa: E402
    HybridComponentsFailedError,
    HybridProtocol,
)
from app.crypto.key_protocol import ProtocolMode, run_exchange  # noqa: E402

_K1 = b"\x11" * 32
_K2 = b"\x22" * 32
_SALT = b"\x33" * 32


class _AlwaysFails:
    """Componente que falha sempre — simula comprometimento (F8.5)."""

    def initiate(self):
        raise RuntimeError("componente comprometido")

    def respond(self, _data):
        return {}

    def get_key(self):
        raise RuntimeError("sem chave")

    def get_metrics(self):
        raise RuntimeError("sem metricas")


# ---------------------------------------------------------------- combiner HKDF
def test_combine_keys_is_deterministic():
    # F16.3: HKDF determinístico para as mesmas entradas.
    assert combine_keys([_K1, _K2], _SALT) == combine_keys([_K1, _K2], _SALT)


def test_combine_keys_output_length():
    assert len(combine_keys([_K1, _K2], _SALT)) == COMBINED_KEY_BYTES


def test_combine_keys_salt_changes_output():
    assert combine_keys([_K1, _K2], _SALT) != combine_keys([_K1, _K2], b"\x44" * 32)


def test_combine_keys_order_matters():
    assert combine_keys([_K1, _K2], _SALT) != combine_keys([_K2, _K1], _SALT)


def test_combine_keys_single_survivor():
    # F8.5: com um unico componente, ikm e a chave desse componente.
    assert len(combine_keys([_K1], _SALT)) == COMBINED_KEY_BYTES


def test_combine_keys_empty_raises():
    with pytest.raises(ValueError):
        combine_keys([], _SALT)


def test_combine_keys_bad_salt_length_raises():
    with pytest.raises(ValueError):
        combine_keys([_K1], b"curto")


def test_generate_salt():
    assert len(generate_salt()) == 32
    assert generate_salt() != generate_salt()


# -------------------------------------------------------------- hybrid protocol
def test_hybrid_exchange_establishes_shared_key():
    initiator, responder = HybridProtocol(), HybridProtocol()
    key_a, key_b = run_exchange(initiator, responder)
    assert key_a == key_b
    assert len(key_a) == 32


def test_hybrid_metrics_both_components_survive():
    initiator, responder = HybridProtocol(), HybridProtocol()
    run_exchange(initiator, responder)
    metrics = initiator.get_metrics()
    assert metrics.mode == ProtocolMode.HYBRID
    assert metrics.key_size_bits == 256
    assert set(metrics.extra["survivors"]) == {"bb84", "mlkem"}


def test_hybrid_survives_bb84_failure(monkeypatch):
    # F8.5: BB84 comprometido -> hibrido continua com ML-KEM.
    monkeypatch.setattr("app.crypto.hybrid.protocol.BB84Protocol", _AlwaysFails)
    initiator, responder = HybridProtocol(), HybridProtocol()
    key_a, key_b = run_exchange(initiator, responder)
    assert key_a == key_b
    assert len(key_a) == 32
    assert initiator.get_metrics().extra["survivors"] == ["mlkem"]


def test_hybrid_survives_mlkem_failure(monkeypatch):
    # F8.5: ML-KEM comprometido -> hibrido continua com BB84.
    monkeypatch.setattr("app.crypto.hybrid.protocol.MLKEMProtocol", _AlwaysFails)
    initiator = HybridProtocol()
    key, _ = run_exchange(initiator, HybridProtocol())
    assert len(key) == 32
    assert initiator.get_metrics().extra["survivors"] == ["bb84"]


def test_hybrid_raises_when_both_components_fail(monkeypatch):
    monkeypatch.setattr("app.crypto.hybrid.protocol.BB84Protocol", _AlwaysFails)
    monkeypatch.setattr("app.crypto.hybrid.protocol.MLKEMProtocol", _AlwaysFails)
    with pytest.raises(HybridComponentsFailedError):
        HybridProtocol().initiate()
