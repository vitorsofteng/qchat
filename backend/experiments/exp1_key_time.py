"""Experimento 1 — tempo de estabelecimento de chave (F17.1).

Mede o tempo de estabelecimento de chave para cada modo, repetido N vezes.
Saida: results/exp1_key_time.csv com colunas mode, key_size, time_ms, run.

Execucao: python -m experiments.exp1_key_time [--runs N]
"""

from __future__ import annotations

import argparse
import os
import time

# Define os qubits do BB84 antes de carregar a configuracao (lru_cache).
os.environ.setdefault("BB84_QUBITS", "1024")

from app.crypto.bb84.protocol import BB84Protocol  # noqa: E402
from app.crypto.hybrid.protocol import HybridProtocol  # noqa: E402
from app.crypto.key_protocol import run_exchange  # noqa: E402
from app.crypto.mlkem.protocol import MLKEMProtocol  # noqa: E402
from app.crypto.rsa.protocol import RSAProtocol  # noqa: E402
from experiments.common import write_csv  # noqa: E402

# (rotulo do modo, key_size relatado, fabrica de uma instancia do protocolo)
_CONFIGS = [
    ("RSA", 2048, RSAProtocol),
    ("MLKEM", 768, lambda: MLKEMProtocol("ML-KEM-768")),
    ("BB84", 1024, lambda: BB84Protocol(n_qubits=1024)),
    ("BB84", 2048, lambda: BB84Protocol(n_qubits=2048)),
    ("HYBRID", 1024, HybridProtocol),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimento 1 — tempo de chave")
    parser.add_argument("--runs", type=int, default=30, help="execucoes por configuracao")
    runs = parser.parse_args().runs

    rows: list[dict] = []
    for mode, key_size, factory in _CONFIGS:
        for run in range(runs):
            try:
                initiator, responder = factory(), factory()
                start = time.perf_counter()
                run_exchange(initiator, responder)
                elapsed_ms = (time.perf_counter() - start) * 1000
            except Exception as exc:
                print(f"  {mode}/{key_size} run {run}: falhou ({exc})")
                continue
            rows.append(
                {
                    "mode": mode,
                    "key_size": key_size,
                    "time_ms": round(elapsed_ms, 3),
                    "run": run,
                }
            )
        print(f"{mode} (key_size={key_size}): {runs} execucoes concluidas")

    path = write_csv("exp1_key_time.csv", ["mode", "key_size", "time_ms", "run"], rows)
    print(f"Resultados salvos em {path}")


if __name__ == "__main__":
    main()
