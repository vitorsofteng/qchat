"""Geracao de graficos publicaveis a partir dos CSVs de experimento (F17.5).

Exporta um PDF vetorial por experimento em experiments/figures/.

Os graficos NAO possuem titulo interno: a legenda (\\caption) e fornecida pelo
documento LaTeX, conforme o padrao ABNT. Rotulos sao apresentados em portugues,
coerentes com as tabelas do TCC.

Execucao: python -m experiments.plot
"""

from __future__ import annotations

from collections import defaultdict

import matplotlib

matplotlib.use("Agg")  # backend sem interface grafica

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from experiments.common import FIGURES_DIR, read_csv  # noqa: E402

# Estilo global consistente entre todas as figuras.
plt.rcParams.update(
    {
        "font.size": 12,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linestyle": "--",
        "figure.dpi": 150,
    }
)

# Rotulos legiveis (coerentes com as tabelas do TCC).
EXP1_LABELS = {
    "MLKEM|768": "ML-KEM-768",
    "HYBRID|1024": "Híbrido\n(1024 qubits)",
    "BB84|1024": "BB84\n(1024 qubits)",
    "BB84|2048": "BB84\n(2048 qubits)",
    "RSA|2048": "RSA\n(2048 bits)",
}
# Ordem por tempo mediano crescente.
EXP1_ORDER = ["MLKEM|768", "HYBRID|1024", "BB84|1024", "BB84|2048", "RSA|2048"]

EXP2_LABELS = {
    "none": "Ausente",
    "IR_total": "Intercept-resend\ntotal",
    "BS_10": "Beam-splitting\n10%",
    "BS_25": "Beam-splitting\n25%",
    "BS_50": "Beam-splitting\n50%",
}
EXP2_ORDER = ["none", "IR_total", "BS_10", "BS_25", "BS_50"]

EXP3_LABELS = {"100B": "100 B", "1KB": "1 KB", "10KB": "10 KB"}
EXP3_ORDER = ["100B", "1KB", "10KB"]

EXP4_LABELS = {
    "both_ok": "Ambos\níntegros",
    "bb84_compromised": "BB84\ncomprometido",
    "mlkem_compromised": "ML-KEM\ncomprometido",
    "both_compromised": "Ambos\ncomprometidos",
}
EXP4_ORDER = ["both_ok", "bb84_compromised", "mlkem_compromised", "both_compromised"]


def _save(figure: plt.Figure, filename: str) -> None:
    FIGURES_DIR.mkdir(exist_ok=True)
    path = FIGURES_DIR / filename
    figure.tight_layout()
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)
    print(f"  -> {path}")


def plot_exp1() -> None:
    rows = read_csv("exp1_key_time.csv")
    if not rows:
        return
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[f"{row['mode']}|{row['key_size']}"].append(float(row["time_ms"]))
    keys = [k for k in EXP1_ORDER if k in groups] or list(groups)
    labels = [EXP1_LABELS.get(k, k) for k in keys]

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.boxplot([groups[k] for k in keys], tick_labels=labels)
    axis.set_yscale("log")
    axis.set_ylabel("Tempo de estabelecimento (ms, escala log.)")
    axis.set_xlabel("Modo de operação (parâmetro interno)")
    _save(figure, "exp1_key_time.pdf")


def plot_exp2() -> None:
    rows = read_csv("exp2_qber.csv")
    if not rows:
        return
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[row["eve_mode"]].append(float(row["qber"]) * 100.0)
    keys = [k for k in EXP2_ORDER if k in groups] or list(groups)
    labels = [EXP2_LABELS.get(k, k) for k in keys]
    means = [float(np.mean(groups[k])) for k in keys]
    stds = [float(np.std(groups[k])) for k in keys]

    figure, axis = plt.subplots(figsize=(8, 5))
    bars = axis.bar(labels, means, yerr=stds, capsize=5, color="steelblue", zorder=3)
    axis.axhline(15.0, color="red", linestyle="--", zorder=4, label="Limiar de detecção (15%)")
    axis.set_ylabel("QBER médio (%)")
    axis.set_xlabel("Modo de adversário (Eve)")
    axis.set_ylim(0, max(35, max(means) + max(stds) + 5))
    for rect, mean in zip(bars, means):
        axis.annotate(
            f"{mean:.1f}",
            xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=10,
        )
    axis.legend()
    _save(figure, "exp2_qber.pdf")


def plot_exp3() -> None:
    rows = read_csv("exp3_throughput.csv")
    if not rows:
        return
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[row["msg_size"]].append(float(row["latency_ms"]))
    keys = [k for k in EXP3_ORDER if k in groups] or list(groups)
    labels = [EXP3_LABELS.get(k, k) for k in keys]

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.boxplot([groups[k] for k in keys], tick_labels=labels)
    axis.set_ylabel("Latência por mensagem (ms)")
    axis.set_xlabel("Tamanho da mensagem")
    _save(figure, "exp3_throughput.pdf")


def plot_exp4() -> None:
    rows = read_csv("exp4_robustness.csv")
    if not rows:
        return
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        groups[row["scenario"]].append(float(row["key_entropy"]))
    keys = [k for k in EXP4_ORDER if k in groups] or list(groups)
    labels = [EXP4_LABELS.get(k, k) for k in keys]
    means = [float(np.mean(groups[k])) for k in keys]

    figure, axis = plt.subplots(figsize=(8, 5))
    bars = axis.bar(labels, means, color="seagreen", zorder=3)
    axis.axhline(5.0, color="gray", linestyle=":", zorder=4, label="Máximo teórico (5 bits/byte)")
    axis.set_ylabel("Entropia de Shannon da chave (bits/byte)")
    axis.set_xlabel("Cenário de comprometimento")
    axis.set_ylim(0, 5.4)
    for rect, mean in zip(bars, means):
        axis.annotate(
            f"{mean:.2f}",
            xy=(rect.get_x() + rect.get_width() / 2, rect.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            fontsize=10,
        )
    axis.legend(loc="upper right")
    _save(figure, "exp4_robustness.pdf")


def main() -> None:
    print("Gerando graficos...")
    plot_exp1()
    plot_exp2()
    plot_exp3()
    plot_exp4()
    print("Concluido.")


if __name__ == "__main__":
    main()
