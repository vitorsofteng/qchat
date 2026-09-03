"""Modelo de adversario simulado — Eve (F11.1 - F11.3).

Modos de ataque ao canal quantico:
  PASSIVE          — Eve nao interfere.
  INTERCEPT_RESEND — Eve mede cada qubit em base aleatoria e reenvia o resultado;
                     introduz QBER ~25%.
  BEAM_SPLITTING   — Eve retem copia de uma fracao dos qubits sem perturbar Bob.

Eve e ativada exclusivamente por configuracao e nunca em producao (F11.4).
"""

from __future__ import annotations

import secrets
from enum import Enum
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from qiskit import QuantumCircuit


class EveMode(str, Enum):
    PASSIVE = "PASSIVE"
    INTERCEPT_RESEND = "INTERCEPT_RESEND"
    BEAM_SPLITTING = "BEAM_SPLITTING"


class EveSimulator:
    """Aplica a interferencia de Eve sobre os qubits em transito."""

    def __init__(
        self,
        mode: EveMode | str = EveMode.PASSIVE,
        beam_split_fraction: float = 0.0,
        rng: secrets.SystemRandom | None = None,
    ) -> None:
        self.mode = EveMode(mode)
        if not 0.0 <= beam_split_fraction <= 1.0:
            raise ValueError("beam_split_fraction deve estar em [0, 1]")
        self.beam_split_fraction = beam_split_fraction
        self._rng = rng or secrets.SystemRandom()
        self.intercepted_count = 0

    @property
    def uses_eve_register(self) -> bool:
        """INTERCEPT_RESEND precisa de um bit classico extra para a medicao de Eve."""
        return self.mode == EveMode.INTERCEPT_RESEND

    def intercept(self, circuit: QuantumCircuit, qubit: int, eve_clbit: int) -> None:
        """Modifica o circuito do qubit em transito conforme o modo de Eve."""
        if self.mode == EveMode.PASSIVE:
            return

        if self.mode == EveMode.INTERCEPT_RESEND:
            eve_basis = self._rng.randint(0, 1)  # 0 = base Z, 1 = base X
            if eve_basis == 1:
                circuit.h(qubit)
            circuit.measure(qubit, eve_clbit)
            if eve_basis == 1:
                circuit.h(qubit)  # reenvia o estado colapsado na base de Eve
            self.intercepted_count += 1
            return

        # BEAM_SPLITTING nao perturba Bob; apenas retem informacao (F11.3).
        if self.mode == EveMode.BEAM_SPLITTING and self._rng.random() < self.beam_split_fraction:
            self.intercepted_count += 1


def configured_eve() -> EveSimulator:
    """Cria a Eve conforme a configuracao do ambiente.

    Eve so e ativada por configuracao e nunca em producao (F11.4): em ambiente
    de producao retorna sempre o modo PASSIVE, independente de `EVE_MODE`.
    """
    settings = get_settings()
    if settings.is_production:
        return EveSimulator(EveMode.PASSIVE)
    return EveSimulator(
        EveMode(settings.eve_mode),
        beam_split_fraction=settings.eve_beam_split_fraction,
    )
