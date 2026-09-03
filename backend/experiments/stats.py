"""Estatistica descritiva e testes t dos experimentos (F17.6).

Le os CSVs de results/ e imprime, para cada experimento, estatistica descritiva
por grupo e testes t comparando os modos.

Execucao: python -m experiments.stats
"""

from __future__ import annotations

import itertools
from collections import defaultdict

import numpy as np
from scipy import stats

from experiments.common import read_csv


def _group(rows: list[dict], key_col: str, value_col: str) -> dict[str, list[float]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[row[key_col]].append(float(row[value_col]))
    return groups


def _describe(label: str, values: list[float]) -> None:
    array = np.asarray(values, dtype=float)
    std = float(array.std(ddof=1)) if len(array) > 1 else 0.0
    print(
        f"  {label:<24} n={len(array):>4}  media={array.mean():>10.4f}  "
        f"dp={std:>10.4f}  min={array.min():>10.4f}  max={array.max():>10.4f}"
    )


def _ttests(groups: dict[str, list[float]]) -> None:
    labels = list(groups)
    for first, second in itertools.combinations(labels, 2):
        if len(groups[first]) < 2 or len(groups[second]) < 2:
            continue
        # Teste t de Welch (nao assume variancias iguais).
        statistic, p_value = stats.ttest_ind(groups[first], groups[second], equal_var=False)
        significant = "significativo" if p_value < 0.05 else "nao significativo"
        print(f"  {first} vs {second}: t={statistic:.3f}  p={p_value:.4g}  ({significant})")


def _section(title: str) -> None:
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def analyze_exp1() -> None:
    rows = read_csv("exp1_key_time.csv")
    if not rows:
        return
    _section("Experimento 1 - tempo de estabelecimento de chave (ms)")
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[f"{row['mode']}-{row['key_size']}"].append(float(row["time_ms"]))
    for label, values in groups.items():
        _describe(label, values)
    print("\n  Testes t (Welch) entre configuracoes:")
    _ttests(groups)


def analyze_exp2() -> None:
    rows = read_csv("exp2_qber.csv")
    if not rows:
        return
    _section("Experimento 2 - QBER por modo de Eve")
    groups = _group(rows, "eve_mode", "qber")
    for label, values in groups.items():
        _describe(label, values)
    print("\n  Testes t (Welch) entre modos de Eve:")
    _ttests(groups)


def analyze_exp3() -> None:
    rows = read_csv("exp3_throughput.csv")
    if not rows:
        return
    _section("Experimento 3 - latencia por tamanho de mensagem (ms)")
    for label, values in _group(rows, "msg_size", "latency_ms").items():
        _describe(label, values)


def analyze_exp4() -> None:
    rows = read_csv("exp4_robustness.csv")
    if not rows:
        return
    _section("Experimento 4 - entropia da chave hibrida (bits/byte)")
    for label, values in _group(rows, "scenario", "key_entropy").items():
        _describe(label, values)


def main() -> None:
    analyze_exp1()
    analyze_exp2()
    analyze_exp3()
    analyze_exp4()
    print()


if __name__ == "__main__":
    main()
