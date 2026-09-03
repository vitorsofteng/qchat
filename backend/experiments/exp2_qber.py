"""Experimento 2 — QBER sob diferentes ataques de Eve (F17.2).

Executa o BB84 sob cada modo de adversario e registra o QBER medido.
Saida: results/exp2_qber.csv com colunas eve_mode, qber, threshold_exceeded, run.

Execucao: python -m experiments.exp2_qber [--runs N]
"""

from __future__ import annotations

import argparse
import os

os.environ.setdefault("BB84_QUBITS", "1024")

from app.crypto.bb84.protocol import QBERThresholdExceeded, run_bb84  # noqa: E402
from app.crypto.eve_simulator import EveMode, EveSimulator  # noqa: E402
from experiments.common import write_csv  # noqa: E402

_QUBITS = 1024
_THRESHOLD = 0.15

# (rotulo, modo de Eve, fracao de beam-splitting)
_EVE_CONFIGS = [
    ("none", EveMode.PASSIVE, 0.0),
    ("IR_total", EveMode.INTERCEPT_RESEND, 0.0),
    ("BS_10", EveMode.BEAM_SPLITTING, 0.10),
    ("BS_25", EveMode.BEAM_SPLITTING, 0.25),
    ("BS_50", EveMode.BEAM_SPLITTING, 0.50),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimento 2 — QBER sob ataque")
    parser.add_argument("--runs", type=int, default=30, help="execucoes por modo de Eve")
    runs = parser.parse_args().runs

    rows: list[dict] = []
    for label, mode, fraction in _EVE_CONFIGS:
        for run in range(runs):
            eve = EveSimulator(mode, beam_split_fraction=fraction)
            try:
                _, result = run_bb84(n_qubits=_QUBITS, qber_threshold=_THRESHOLD, eve=eve)
                qber, exceeded = result.qber, False
            except QBERThresholdExceeded as exc:
                qber, exceeded = exc.qber, True
            rows.append(
                {
                    "eve_mode": label,
                    "qber": round(qber, 4),
                    "threshold_exceeded": exceeded,
                    "run": run,
                }
            )
        print(f"Eve={label}: {runs} execucoes concluidas")

    path = write_csv("exp2_qber.csv", ["eve_mode", "qber", "threshold_exceeded", "run"], rows)
    print(f"Resultados salvos em {path}")


if __name__ == "__main__":
    main()
