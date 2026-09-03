# Experimentos — QChat

Os quatro experimentos alimentam o Capítulo 4 do TCC. Os scripts estão em
`backend/experiments/` e exercitam diretamente os módulos criptográficos.

## Pré-requisitos

```bash
cd backend
pip install -e ".[dev,quantum,experiments]"
```

O extra `experiments` traz `matplotlib` (gráficos) e `scipy` (estatística).

## Execução

A partir da raiz do repositório:

```bash
make experiments   # roda os 4 experimentos e gera os gráficos
make stats         # estatística descritiva + teste t sobre os CSVs
```

Ou individualmente, a partir de `backend/`:

```bash
python -m experiments.exp1_key_time --runs 30
python -m experiments.exp2_qber --runs 30
python -m experiments.exp3_throughput --messages 1000
python -m experiments.exp4_robustness --runs 30
python -m experiments.plot
python -m experiments.stats
```

Saídas: CSVs em `backend/experiments/results/`, gráficos PDF em
`backend/experiments/figures/`.

## Os quatro experimentos

### Experimento 1 — tempo de estabelecimento de chave

Mede o tempo de estabelecimento para cada modo, repetido N vezes.
**Saída:** `exp1_key_time.csv` — `mode, key_size, time_ms, run`.

### Experimento 2 — QBER sob ataque

Executa o BB84 sob cada modo de adversário (`none`, `IR_total`, `BS_10`,
`BS_25`, `BS_50`) e registra o QBER medido.
**Saída:** `exp2_qber.csv` — `eve_mode, qber, threshold_exceeded, run`.

Resultado esperado: QBER ≈ 0 sem espião; ≈ 25% sob *intercept-resend*
(detectado); ≈ 0 sob *beam-splitting* (não perturba, mas vaza informação).

### Experimento 3 — throughput de mensagens

Com a chave estabelecida, mede a latência de cifrar+decifrar mensagens de
tamanhos {100 B, 1 KB, 10 KB}.
**Saída:** `exp3_throughput.csv` — `msg_size, latency_ms, throughput_msgs_s`.

### Experimento 4 — robustez do híbrido

Para cada execução, BB84 e ML-KEM produzem chaves componentes reais; em seguida
são simulados quatro cenários de comprometimento. Valida que o híbrido sobrevive
enquanto ao menos um componente permanecer íntegro.
**Saída:** `exp4_robustness.csv` — `scenario, key_established, key_entropy`.

## Reprodutibilidade

Os scripts aceitam `--runs` / `--messages` para ajustar o número de execuções.
Os modos BB84/Híbrido usam `BB84_QUBITS=1024` por padrão nos experimentos
(definido no início de cada script) para manter o tempo total tratável; ajuste
para 4096 caso queira reproduzir as condições nominais do sistema.
