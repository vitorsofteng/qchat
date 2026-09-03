"""Testes baseados em propriedades dos modulos criptograficos puros (F16.6).

Cobrem amplificacao de privacidade e o combinador HKDF — nao dependem do Qiskit.
"""

import secrets

from hypothesis import given
from hypothesis import strategies as st

from app.crypto.bb84.privacy_amp import final_key_length, privacy_amplify
from app.crypto.hybrid.combiner import COMBINED_KEY_BYTES, combine_keys

_RNG = secrets.SystemRandom()


@given(
    bits=st.lists(st.integers(min_value=0, max_value=1), min_size=1, max_size=600),
    qber=st.floats(min_value=0.0, max_value=0.4),
)
def test_privacy_amplification_output_length_matches_shor_preskill(bits, qber):
    """Para qualquer chave reconciliada, |saida| = floor(n * (1 - 2*h2(Q)))."""
    output = privacy_amplify(bits, qber, _RNG)
    assert len(output) == final_key_length(len(bits), qber)
    assert all(bit in (0, 1) for bit in output)


@given(
    first=st.binary(min_size=1, max_size=64),
    second=st.binary(min_size=1, max_size=64),
    salt=st.binary(min_size=32, max_size=32),
)
def test_hkdf_combiner_always_produces_32_byte_key(first, second, salt):
    """Para quaisquer chaves componentes, o HKDF produz uma chave de 32 bytes."""
    assert len(combine_keys([first, second], salt)) == COMBINED_KEY_BYTES


@given(
    first=st.binary(min_size=1, max_size=64),
    second=st.binary(min_size=1, max_size=64),
    salt=st.binary(min_size=32, max_size=32),
)
def test_hkdf_combiner_is_deterministic(first, second, salt):
    """Mesmas entradas sempre derivam a mesma chave hibrida."""
    assert combine_keys([first, second], salt) == combine_keys([first, second], salt)
