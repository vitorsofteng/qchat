"""Reconciliacao de erros pelo protocolo Cascade (F6.8).

Brassard & Salvail (1993). Quatro passes; o tamanho de bloco inicial e funcao do
QBER estimado e dobra a cada pass. Cada bloco com paridade discrepante tem um
erro localizado e corrigido por busca binaria. Ao corrigir um bit, os blocos de
passes anteriores que o contem sao reavaliados — o efeito "cascata" que da nome
ao protocolo.
"""

from __future__ import annotations

import math
import secrets
from collections import deque


def initial_block_size(qber: float, total: int) -> int:
    """Tamanho de bloco do primeiro pass: k1 = ceil(0.73 / Q) (Brassard & Salvail)."""
    if qber <= 0.0:
        return max(1, total)
    k = math.ceil(0.73 / qber)
    return max(1, min(k, total))


def reconcile(
    alice_bits: list[int],
    bob_bits: list[int],
    *,
    qber: float,
    passes: int = 4,
    rng: secrets.SystemRandom | None = None,
) -> tuple[list[int], int]:
    """Corrige ``bob_bits`` para coincidir com ``alice_bits``.

    Retorna ``(bits_corrigidos, bits_de_paridade_revelados)``.
    """
    if len(alice_bits) != len(bob_bits):
        raise ValueError("Sequencias de Alice e Bob com tamanhos diferentes")

    rng = rng or secrets.SystemRandom()
    bob = list(bob_bits)
    n = len(bob)
    if n == 0:
        return bob, 0

    leaked = 0
    pass_blocks: list[list[tuple[int, ...]]] = []
    membership: list[list[tuple[int, int]]] = [[] for _ in range(n)]

    def error_parity(indices: tuple[int, ...]) -> int:
        diff = 0
        for i in indices:
            diff ^= alice_bits[i] ^ bob[i]
        return diff

    def binary_correct(indices: tuple[int, ...]) -> int:
        """Localiza e corrige um erro num bloco de paridade impar. Retorna o indice."""
        nonlocal leaked
        block = list(indices)
        while len(block) > 1:
            mid = len(block) // 2
            leaked += 1  # revela a paridade da metade esquerda
            error_in_left = error_parity(tuple(block[:mid])) == 1
            block = block[:mid] if error_in_left else block[mid:]
        index = block[0]
        bob[index] ^= 1
        return index

    block_size = initial_block_size(qber, n)
    for pass_index in range(passes):
        order = list(range(n))
        rng.shuffle(order)
        blocks = [tuple(order[s : s + block_size]) for s in range(0, n, block_size)]
        pass_blocks.append(blocks)
        for position, block in enumerate(blocks):
            for i in block:
                membership[i].append((pass_index, position))

        odd_blocks: deque[tuple[int, int]] = deque()
        for position, block in enumerate(blocks):
            leaked += 1  # revela a paridade do bloco
            if error_parity(block) == 1:
                odd_blocks.append((pass_index, position))

        while odd_blocks:
            block_pass, block_pos = odd_blocks.popleft()
            block = pass_blocks[block_pass][block_pos]
            if error_parity(block) == 0:
                continue  # ja corrigido por uma cascata anterior
            flipped = binary_correct(block)
            for other_pass, other_pos in membership[flipped]:
                if (other_pass, other_pos) == (block_pass, block_pos):
                    continue
                leaked += 1
                if error_parity(pass_blocks[other_pass][other_pos]) == 1:
                    odd_blocks.append((other_pass, other_pos))

        block_size *= 2

    return bob, leaked
