# QChat — Backend

Servidor FastAPI do sistema de chat hibrido QKD+PQC.

## Requisitos

- Python 3.11+
- (Opcional) extras `quantum` para os modos BB84/ML-KEM/Hibrido

## Setup de desenvolvimento

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -e ".[dev]"
# Para os modos quanticos (BB84, ML-KEM, Hibrido):
pip install -e ".[dev,quantum]"

cp ../.env.example ../.env   # ajuste o JWT_SECRET
```

## Rodar

```bash
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000
- Documentacao OpenAPI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Testes

```bash
pytest
coverage run -m pytest && coverage report
```

## Qualidade

```bash
ruff check app tests
black app tests
```

## Estrutura

```
app/
  main.py            entry point FastAPI
  api/               rotas HTTP + WebSocket
  core/              config, seguranca, session manager
  crypto/            protocolos de estabelecimento de chave
  monitor/           monitor de QBER + observers
  models/            modelos SQLAlchemy
  schemas/           schemas Pydantic
```
