"""Utilitarios compartilhados dos scripts de experimento (F17)."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

_EXPERIMENTS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _EXPERIMENTS_DIR / "results"
FIGURES_DIR = _EXPERIMENTS_DIR / "figures"


def write_csv(filename: str, fieldnames: list[str], rows: list[dict[str, Any]]) -> Path:
    """Escreve as linhas em results/<filename> e retorna o caminho."""
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / filename
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def read_csv(filename: str) -> list[dict[str, str]]:
    """Le results/<filename>. Retorna lista vazia se o arquivo nao existir."""
    path = RESULTS_DIR / filename
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))
