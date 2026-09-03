# Guia de Implantação — QChat

Este documento descreve como subir o QChat localmente (para avaliação) e em
produção.

## Sumário

- [Pré-requisitos](#pré-requisitos)
- [Opção A — execução local sem Docker (verificada)](#opção-a--execução-local-sem-docker)
- [Opção B — Docker Compose](#opção-b--docker-compose)
- [Produção](#produção)

---

## Pré-requisitos

| Opção | Necessário |
|---|---|
| Local | Python 3.11+, Node 20+ |
| Docker | Docker + Docker Compose |

> O modo **RSA** funciona com a instalação base. Os modos **ML-KEM**, **BB84** e
> **Híbrido** exigem os extras `quantum` (qiskit-aer, liboqs-python). O liboqs é
> compilado na primeira instalação — exige `cmake` e um compilador C.

---

## Opção A — execução local sem Docker

Caminho **verificado**, recomendado para a avaliação da banca. Dois terminais.

### Terminal 1 — backend

```bash
cd backend
python -m venv .venv
# Windows:        .venv\Scripts\activate
# Linux / macOS:  source .venv/bin/activate

pip install -e ".[dev,quantum]"     # base + ferramentas + 4 modos
uvicorn app.main:app --port 8000
```

Backend em http://localhost:8000 — documentação interativa em `/docs`.

### Terminal 2 — frontend

```bash
cd frontend
npm install
npm start
```

Aplicação em **http://localhost:4200**.

> A primeira instalação leva alguns minutos (a compilação do liboqs é a etapa
> mais lenta). Execuções seguintes são rápidas.

---

## Opção B — Docker Compose

Sobe banco + backend + frontend com um comando:

```bash
docker compose up --build
```

- Frontend: http://localhost:4200
- Backend: http://localhost:8000

> **Primeiro build é demorado** (~10–15 min): a imagem do backend compila
> `liboqs` e instala o Qiskit. Os `docker compose up` seguintes são rápidos.
> Para iterar mais rápido durante o desenvolvimento, prefira a Opção A.

---

## Produção

Use `docker-compose.prod.yml`: apenas o nginx publica portas; backend, frontend
e banco ficam em redes internas isoladas.

### 1. Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
JWT_SECRET=<segredo-forte-aleatorio>
POSTGRES_PASSWORD=<senha-do-banco>
PUBLIC_URL=https://seu-dominio.exemplo
```

### 2. Subir a stack

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

A aplicação fica disponível na porta 80. O nginx serve o frontend e encaminha
`/api` e `/ws` para o backend.

### 3. TLS (HTTPS)

1. Obtenha os certificados — **Let's Encrypt** (`certbot`) em produção ou
   **mkcert** em desenvolvimento.
2. Coloque `fullchain.pem` e `privkey.pem` em `nginx/certs/`.
3. Em [`nginx/nginx.conf`](nginx/nginx.conf), descomente o bloco `server` da
   porta 443.
4. Em [`docker-compose.prod.yml`](docker-compose.prod.yml), descomente a porta
   `443:443` e o volume `./nginx/certs`.
5. Recarregue: `docker compose -f docker-compose.prod.yml up -d`.

### 4. Hospedagem

Plataformas adequadas para o artefato: **Hetzner CX22** (~€5/mês), **Fly.io**
(free tier) ou **Railway**. Aponte o domínio para o servidor e siga os passos
de TLS acima.

---

## Health checks

| Endpoint | Serviço |
|---|---|
| `GET /health` | backend (status, versão) |
| `GET /healthz` | nginx (proxy reverso) |
| `GET /config` | parâmetros públicos do sistema |
