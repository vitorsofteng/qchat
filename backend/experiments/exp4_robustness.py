"""Experimento 4 — robustez do esquema hibrido (F17.4).

Para cada execucao, BB84 e ML-KEM produzem chaves componentes reais. Em seguida
sao simulados quatro cenarios de comprometimento, e a chave hibrida resultante
e avaliada. Valida a propriedade de F8.5: o hibrido sobrevive enquanto ao menos
um componente permanecer integro.

Saida: results/exp4_robustness.csv com colunas scenario, key_established, key_entropy.

Execucao: python -m experiments.exp4_robustness [--runs N]
"""

from __future__ import annotations

import argparse
import math
import os
from collections import Counter

os.environ.setdefault("BB84_QUBITS", "1024")

from app.crypto.bb84.protocol import BB84Protocol  # noqa: E402
from app.crypto.hybrid.combiner import combine_keys, generate_salt  # noqa: E402
from app.crypto.key_protocol import run_exchange  # noqa: E402
from app.crypto.mlkem.protocol import MLKEMProtocol  # noqa: E402
from experiments.common import write_csv  # noqa: E402


def shannon_entropy(data: bytes) -> float:
    """Entropia de Shannon (bits/byte) dos bytes da chave."""
    if not data:
        return 0.0
    total = len(data)
    return -sum((count / total) * math.log2(count / total) for count in Counter(data).values())


def main() -> None:
    parser = argparse.ArgumentParser(description="Experimento 4 — robustez do hibrido")
    parser.add_argument("--runs", type=int, default=30, help="execucoes")
    runs = parser.parse_args().runs

    rows: list[dict] = []
    for run in range(runs):
        key_bb84, _ = run_exchange(BB84Protocol(n_qubits=1024), BB84Protocol(n_qubits=1024))
        key_mlkem, _ = run_exchange(MLKEMProtocol(), MLKEMProtocol())
        salt = generate_salt()

        # Cenario -> componentes sobreviventes.
        scenarios = {
            "both_ok": [key_bb84, key_mlkem],
            "bb84_compromised": [key_mlkem],
            "mlkem_compromised": [key_bb84],
            "both_compromised": [],
        }
        for scenario, surviving in scenarios.items():
            if surviving:
                final_key = combine_keys(surviving, salt)
                established, entropy = True, shannon_entropy(final_key)
            else:
                established, entropy = False, 0.0
            rows.append(
                {
                    "scenario": scenario,
                    "key_established": established,
                    "key_entropy": round(entropy, 4),
                }
            )
        if (run + 1) % 10 == 0:
            print(f"  {run + 1}/{runs} execucoes")

    path = write_csv("exp4_robustness.csv", ["scenario", "key_established", "key_entropy"], rows)
    print(f"Resultados salvos em {path}")


if __name__ == "__main__":
    main()
