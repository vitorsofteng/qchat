"""Estimativa de QBER (F6.6).

Reserva e revela uma amostra da chave sifted; o QBER e a fracao de discrepancias
nessa amostra. Os bits revelados sao descartados da chave.
"""

from __future__ import annotations

import secrets

DEFAULT_SAMPLE_FRACTION = 0.25


def estimate_qber(
    sifted_alice: list[int],
    sifted_bob: list[int],
    sample_fraction: float = DEFAULT_SAMPLE_FRACTION,
    rng: secrets.SystemRandom | None = None,
) -> tuple[float, list[int], list[int]]:
    """Mede o QBER sobre uma amostra aleatoria.

    Retorna ``(qber, restante_alice, restante_bob)``. A amostra e descartada por
    ter sido revelada pelo canal classico.
    """
    if len(sifted_alice) != len(sifted_bob):
        raise ValueError("Chaves sifted de Alice e Bob com tamanhos diferentes")
    if not 0.0 < sample_fraction < 1.0:
        raise ValueError("sample_fraction deve estar em (0, 1)")

    rng = rng or secrets.SystemRandom()
    n = len(sifted_alice)
    sample_size = int(n * sample_fraction)
    if sample_size == 0:
        return 0.0, list(sifted_alice), list(sifted_bob)

    sample_indices = set(rng.sample(range(n), sample_size))
    mismatches = sum(1 for i in sample_indices if sifted_alice[i] != sifted_bob[i])
    qber = mismatches / sample_size

    remaining_alice = [sifted_alice[i] for i in range(n) if i not in sample_indices]
    remaining_bob = [sifted_bob[i] for i in range(n) if i not in sample_indices]
    return qber, remaining_alice, remaining_bob
