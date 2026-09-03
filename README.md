# QChat — Sistema de Mensageria Híbrida Resistente a Computadores Quânticos

[![CI](https://github.com/vitorsofteng/qchat/actions/workflows/ci.yml/badge.svg)](https://github.com/vitorsofteng/qchat/actions/workflows/ci.yml)
![Cobertura](https://img.shields.io/badge/cobertura%20cripto-%E2%89%A585%25-brightgreen)
![Licença](https://img.shields.io/badge/licença-MIT-blue)

Prova de conceito de mensageria 1-para-1, com mensagens efêmeras e quatro modos
de estabelecimento de chave selecionáveis:

| Modo | Descrição |
|---|---|
| **BB84** | Distribuição de Chaves Quânticas (QKD) — pipeline completo |
| **ML-KEM** | Criptografia Pós-Quântica (PQC) — NIST FIPS 203 |
| **Híbrido** | BB84 + ML-KEM combinados via HKDF |
| **RSA** | Criptografia clássica — controle experimental |

Cada modo produz uma chave AES-256-GCM que cifra as mensagens da sessão.
Artefato experimental de Trabalho de Conclusão de Curso.

## Stack

- **Backend:** Python 3.11, FastAPI, Qiskit Aer, liboqs-python, PyCryptodome, cryptography
- **Frontend:** Angular 21 (standalone + signals), Angular Material
- **Comunicação:** HTTPS/WSS, JSON
- **Infra:** Docker, nginx, GitHub Actions

## Rodar localmente

### Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev,quantum]"                  # base + 4 modos
uvicorn app.main:app --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

Aplicação em **http://localhost:4200** · API em http://localhost:8000 ·
documentação interativa em http://localhost:8000/docs

Passos detalhados (incluindo Docker e produção) em [DEPLOY.md](DEPLOY.md).

## Estrutura

```
backend/      API FastAPI, protocolos criptográficos, experimentos
frontend/     aplicação Angular
nginx/        proxy reverso de produção
docs/         especificação de features e documento de negócio (TCC)
```

## Documentação

- [Arquitetura](ARCHITECTURE.md) — componentes e decisões técnicas
- [Implantação](DEPLOY.md) — execução local e produção
- [Experimentos](EXPERIMENTS.md) — como reproduzir os 4 experimentos
- [Changelog](CHANGELOG.md)
- [Backend](backend/README.md) · [Frontend](frontend/README.md)

## Testes

```bash
cd backend && pytest          # suíte do backend (cobertura ≥ 85% em crypto/)
cd frontend && npm run lint   # lint do frontend
```

## Licença

[MIT](LICENSE)
