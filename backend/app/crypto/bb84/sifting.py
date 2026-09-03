"""Sifting BB84 (F6.5).

Alice e Bob trocam as bases pelo canal classico e retem apenas os bits das
posicoes em que as bases coincidem.
"""

from __future__ import annotations


def sift(
    alice_bases: list[int],
    bob_bases: list[int],
    alice_bits: list[int],
    bob_bits: list[int],
) -> tuple[list[int], list[int]]:
    """Retorna (chave_sifted_alice, chave_sifted_bob) das bases coincidentes."""
    if not len(alice_bases) == len(bob_bases) == len(alice_bits) == len(bob_bits):
        raise ValueError("Todas as sequencias devem ter o mesmo comprimento")

    sifted_alice: list[int] = []
    sifted_bob: list[int] = []
    for a_basis, b_basis, a_bit, b_bit in zip(
        alice_bases, bob_bases, alice_bits, bob_bits, strict=True
    ):
        if a_basis == b_basis:
            sifted_alice.append(a_bit)
            sifted_bob.append(b_bit)
    return sifted_alice, sifted_bob
