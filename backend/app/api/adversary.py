"""Controle do adversario simulado, para demonstracao interativa (F11.4).

Permite alternar o modo de Eve em tempo de execucao, sem reiniciar o servico.
O adversario continua bloqueado em producao: la' o modo e' sempre PASSIVE e
qualquer tentativa de alteracao e' recusada.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.core.config import get_settings
from app.crypto.eve_simulator import (
    EveMode,
    adversary_locked,
    current_adversary_mode,
    set_adversary_mode,
)

router = APIRouter(prefix="/adversary", tags=["adversary"])

_DESCRIPTIONS: dict[EveMode, str] = {
    EveMode.PASSIVE: "Sem espionagem — canal integro.",
    EveMode.INTERCEPT_RESEND: (
        "Eve mede cada qubit em base aleatoria e reenvia o resultado. Perturba o "
        "canal e eleva o QBER para cerca de 25%."
    ),
    EveMode.BEAM_SPLITTING: (
        "Eve retem uma fracao dos qubits sem perturbar Bob: nao eleva o QBER, "
        "mas vaza informacao."
    ),
}


class AdversaryOption(BaseModel):
    mode: EveMode
    description: str


class AdversaryState(BaseModel):
    """Situacao do adversario simulado e as opcoes disponiveis."""

    mode: EveMode
    description: str
    beam_split_fraction: float
    # Em producao o controle e' somente leitura.
    locked: bool
    options: list[AdversaryOption]


class AdversaryUpdate(BaseModel):
    mode: EveMode


def _state() -> AdversaryState:
    mode = current_adversary_mode()
    return AdversaryState(
        mode=mode,
        description=_DESCRIPTIONS[mode],
        beam_split_fraction=get_settings().eve_beam_split_fraction,
        locked=adversary_locked(),
        options=[
            AdversaryOption(mode=option, description=_DESCRIPTIONS[option]) for option in EveMode
        ],
    )


@router.get("", response_model=AdversaryState)
def read_adversary(_current_user: CurrentUser) -> AdversaryState:
    """Modo do adversario em vigor."""
    return _state()


@router.put("", response_model=AdversaryState)
def update_adversary(body: AdversaryUpdate, _current_user: CurrentUser) -> AdversaryState:
    """Troca o adversario. Vale a partir da proxima sessao estabelecida."""
    try:
        set_adversary_mode(body.mode)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return _state()
