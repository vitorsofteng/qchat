"""Amplificacao de privacidade (F6.9).

Hashing universal por matriz de Toeplitz aleatoria. O comprimento da chave final
e dado pela formula de Shor-Preskill: l = n * (1 - 2 * h2(Q)).
"""

from __future__ import annotations

import math
import secrets


def binary_entropy(q: float) -> float:
    """Entropia binaria h2(q) = -q*log2(q) - (1-q)*log2(1-q)."""
    if q <= 0.0 or q >= 1.0:
        return 0.0
    return -q * math.log2(q) - (1.0 - q) * math.log2(1.0 - q)


def final_key_length(reconciled_length: int, qber: float) -> int:
    """Comprimento da chave final (Shor-Preskill): l = floor(n*(1 - 2*h2(Q)))."""
    length = math.floor(reconciled_length * (1.0 - 2.0 * binary_entropy(qber)))
    return max(0, length)


def toeplitz_hash(bits: list[int], output_length: int, rng: secrets.SystemRandom) -> list[int]:
    """Hashing universal por matriz de Toeplitz m x n (n bits -> output_length bits).

    A matriz de Toeplitz fica definida por m + n - 1 bits aleatorios: o elemento
    T[i][j] depende apenas de i - j.
    """
    n = len(bits)
    if output_length <= 0 or n == 0:
        return []

    diagonals = [rng.getrandbits(1) for _ in range(output_length + n - 1)]
    output: list[int] = []
    for row in range(output_length):
        base = row + n - 1
        acc = 0
        for col in range(n):
            acc ^= diagonals[base - col] & bits[col]
        output.append(acc)
    return output


def privacy_amplify(
    reconciled_bits: list[int],
    qber: float,
    rng: secrets.SystemRandom | None = None,
) -> list[int]:
    """Comprime a chave reconciliada para l = floor(n*(1 - 2*h2(Q))) bits."""
    rng = rng or secrets.SystemRandom()
    length = final_key_length(len(reconciled_bits), qber)
    return toeplitz_hash(reconciled_bits, length, rng)
