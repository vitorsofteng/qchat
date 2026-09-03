"""Testes dos componentes puros do pipeline BB84 (F16.1).

Cobrem sifting, estimativa de QBER, reconciliacao Cascade e amplificacao de
privacidade — nao dependem do Qiskit.
"""

import math
import secrets

import pytest

from app.crypto.bb84.cascade import initial_block_size, reconcile
from app.crypto.bb84.privacy_amp import (
    binary_entropy,
    final_key_length,
    privacy_amplify,
    toeplitz_hash,
)
from app.crypto.bb84.qber import estimate_qber
from app.crypto.bb84.sifting import sift
from app.crypto.eve_simulator import EveMode, EveSimulator, configured_eve

RNG = secrets.SystemRandom()


# --------------------------------------------------------------------- sifting
def test_sift_keeps_only_matching_bases():
    alice_bases = [0, 1, 0, 1]
    bob_bases = [0, 0, 0, 1]
    alice_bits = [1, 1, 0, 0]
    bob_bits = [1, 0, 0, 0]
    sifted_alice, sifted_bob = sift(alice_bases, bob_bases, alice_bits, bob_bits)
    assert sifted_alice == [1, 0, 0]  # posicoes 0, 2, 3
    assert sifted_bob == [1, 0, 0]


def test_sift_no_matching_bases():
    sifted_alice, sifted_bob = sift([0, 0], [1, 1], [1, 1], [0, 0])
    assert sifted_alice == []
    assert sifted_bob == []


def test_sift_length_mismatch_raises():
    with pytest.raises(ValueError):
        sift([0], [0, 1], [0], [0])


# ------------------------------------------------------------------------ QBER
def test_qber_zero_when_keys_identical():
    bits = [RNG.randint(0, 1) for _ in range(400)]
    qber, remaining_alice, remaining_bob = estimate_qber(bits, list(bits))
    assert qber == 0.0
    assert remaining_alice == remaining_bob


def test_qber_detects_introduced_errors():
    n = 400
    alice = [0] * n
    bob = [0] * n
    for i in range(0, n, 4):  # 25% dos bits invertidos
        bob[i] = 1
    qber, _, _ = estimate_qber(alice, bob)
    assert 0.15 < qber < 0.35


def test_qber_sample_removed_from_remaining():
    bits = [0] * 100
    _, remaining_alice, _ = estimate_qber(bits, bits, sample_fraction=0.25)
    assert len(remaining_alice) == 75


# --------------------------------------------------------------------- Cascade
def test_cascade_corrects_all_errors():
    # n grande: o residuo de Cascade de 4 passes (pares de erros co-localizados
    # em todos os passes) fica negligenciavel.
    n = 3000
    alice = [RNG.randint(0, 1) for _ in range(n)]
    for error_rate in (0.03, 0.07, 0.12):
        bob = list(alice)
        for i in RNG.sample(range(n), int(n * error_rate)):
            bob[i] ^= 1
        corrected, leaked = reconcile(alice, bob, qber=error_rate, passes=4, rng=RNG)
        assert corrected == alice, f"falhou em taxa de erro {error_rate}"
        assert leaked > 0


def test_cascade_no_errors_is_noop():
    alice = [RNG.randint(0, 1) for _ in range(200)]
    corrected, _ = reconcile(alice, list(alice), qber=0.0, passes=4, rng=RNG)
    assert corrected == alice


def test_initial_block_size():
    assert initial_block_size(0.1, 1000) == 8  # ceil(0.73 / 0.1)
    assert initial_block_size(0.0, 1000) == 1000


# ----------------------------------------------------- amplificacao de privacidade
def test_binary_entropy_known_values():
    assert binary_entropy(0.0) == 0.0
    assert binary_entropy(1.0) == 0.0
    assert binary_entropy(0.5) == pytest.approx(1.0)


def test_final_key_length_shor_preskill():
    assert final_key_length(1000, 0.0) == 1000
    q = 0.05
    expected = math.floor(1000 * (1 - 2 * binary_entropy(q)))
    assert final_key_length(1000, q) == expected


def test_privacy_amplify_output_length_matches_formula():
    # F16.6: tamanho final = floor(n * (1 - 2*h2(Q))).
    bits = [RNG.randint(0, 1) for _ in range(500)]
    for q in (0.0, 0.03, 0.08):
        amplified = privacy_amplify(bits, q, RNG)
        assert len(amplified) == final_key_length(500, q)


def test_toeplitz_hash_output_is_binary():
    bits = [RNG.randint(0, 1) for _ in range(64)]
    output = toeplitz_hash(bits, 20, RNG)
    assert len(output) == 20
    assert all(bit in (0, 1) for bit in output)


def test_toeplitz_hash_zero_length():
    assert toeplitz_hash([1, 0, 1], 0, RNG) == []


# ---------------------------------------------------------------- Eve simulator
def test_configured_eve_defaults_to_passive():
    # Em ambiente de teste EVE_MODE nao esta definido (F11.4).
    assert configured_eve().mode == EveMode.PASSIVE


def test_eve_simulator_rejects_invalid_fraction():
    with pytest.raises(ValueError):
        EveSimulator(EveMode.BEAM_SPLITTING, beam_split_fraction=1.5)


def test_eve_uses_register_only_for_intercept_resend():
    assert EveSimulator(EveMode.INTERCEPT_RESEND).uses_eve_register is True
    assert EveSimulator(EveMode.PASSIVE).uses_eve_register is False
