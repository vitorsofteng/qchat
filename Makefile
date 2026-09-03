# QChat — automacao de tarefas de desenvolvimento e experimentos.

.PHONY: experiments stats test lint

# Roda os 4 experimentos e gera os graficos (F17.7).
experiments:
	cd backend && python -m experiments.exp1_key_time
	cd backend && python -m experiments.exp2_qber
	cd backend && python -m experiments.exp3_throughput
	cd backend && python -m experiments.exp4_robustness
	cd backend && python -m experiments.plot

# Estatistica descritiva e testes t sobre os CSVs gerados.
stats:
	cd backend && python -m experiments.stats

# Suite de testes do backend.
test:
	cd backend && pytest

# Lint e verificacao de formatacao.
lint:
	cd backend && ruff check app tests experiments
	cd backend && black --check app tests experiments
