"""Testes baseados em propriedades do pipeline BB84 (F16.6).

Cada exemplo executa o BB84 com Qiskit (custoso) — o numero de exemplos do
hypothesis e reduzido. Pulados quando o extra `qkd` nao esta instalado.
"""

import pytest

pytest.importorskip("qiskit_aer", reason="extra 'qkd' (qiskit) nao instalado")

from hypothesis import HealthCheck, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

from app.crypto.bb84.protocol import QBERThresholdExceeded, run_bb84  # noqa: E402
from app.crypto.eve_simulator import EveMode, EveSimulator  # noqa: E402

_SLOW = settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.too_slow])


@_SLOW
@given(n_qubits=st.integers(min_value=1024, max_value=2048))
def test_bb84_without_eve_has_negligible_qber(n_qubits):
    """Sem Eve, o canal ideal nao introduz erros — QBER < 1%."""
    _, result = run_bb84(n_qubits=n_qubits, qber_threshold=0.15)
    assert result.qber < 0.01


@_SLOW
@given(n_qubits=st.integers(min_value=1024, max_value=2048))
def test_bb84_intercept_resend_qber_near_25_percent(n_qubits):
    """Sob intercept-resend, o QBER fica em torno de 25% e e detectado."""
    eve = EveSimulator(EveMode.INTERCEPT_RESEND)
    with pytest.raises(QBERThresholdExceeded) as exc_info:
        run_bb84(n_qubits=n_qubits, qber_threshold=0.15, eve=eve)
    assert 0.15 < exc_info.value.qber < 0.40
