"""Testes do pipeline BB84 ponta a ponta com Qiskit Aer (F16.1).

Pulados quando o extra `qkd` (qiskit) nao esta instalado.
"""

import pytest

pytest.importorskip("qiskit_aer", reason="extra 'qkd' (qiskit) nao instalado")

from app.crypto.bb84.protocol import (  # noqa: E402
    BB84Protocol,
    InsufficientKeyMaterial,
    QBERThresholdExceeded,
    run_bb84,
)
from app.crypto.eve_simulator import EveMode, EveSimulator  # noqa: E402
from app.crypto.key_protocol import ProtocolMode  # noqa: E402


def test_bb84_without_eve_establishes_key():
    key, result = run_bb84(n_qubits=1024, qber_threshold=0.15)
    assert len(key) == 32
    assert result.qber == 0.0  # simulador ideal, sem ruido de canal
    assert result.sifted_length > 0
    assert result.amplified_length >= 256


def test_bb84_intercept_resend_raises_with_high_qber():
    eve = EveSimulator(EveMode.INTERCEPT_RESEND)
    with pytest.raises(QBERThresholdExceeded) as exc_info:
        run_bb84(n_qubits=1024, qber_threshold=0.15, eve=eve)
    # Intercept-resend introduz QBER ~25%.
    assert 0.15 < exc_info.value.qber < 0.40
    assert eve.intercepted_count == 1024


def test_bb84_beam_splitting_does_not_perturb_bob():
    eve = EveSimulator(EveMode.BEAM_SPLITTING, beam_split_fraction=0.5)
    key, result = run_bb84(n_qubits=1024, qber_threshold=0.15, eve=eve)
    assert len(key) == 32
    assert result.qber == 0.0  # beam-splitting nao perturba a medicao de Bob


def test_bb84_protocol_initiator_and_responder_share_key():
    initiator = BB84Protocol(n_qubits=1024)
    message = initiator.initiate()
    responder = BB84Protocol()
    responder.respond(message)
    assert initiator.get_key() == responder.get_key()
    assert len(initiator.get_key()) == 32


def test_bb84_protocol_metrics():
    protocol = BB84Protocol(n_qubits=1024)
    protocol.initiate()
    metrics = protocol.get_metrics()
    assert metrics.mode == ProtocolMode.BB84
    assert metrics.qber == 0.0
    assert metrics.key_size_bits == 256
    assert metrics.elapsed_ms > 0
    assert metrics.extra["n_qubits"] == 1024


def test_bb84_insufficient_qubits_raises():
    with pytest.raises(InsufficientKeyMaterial):
        run_bb84(n_qubits=64, qber_threshold=0.15)


def test_bb84_get_key_before_run_raises():
    with pytest.raises(RuntimeError):
        BB84Protocol().get_key()
