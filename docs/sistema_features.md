# Sistema de Chat Híbrido QKD+PQC — Especificação Técnica

Sistema de mensageria 1-para-1 com mensagens efêmeras e quatro modos de estabelecimento de chave selecionáveis: BB84, ML-KEM, Híbrido (BB84+ML-KEM via HKDF) e RSA (controle). Cada modo produz uma chave AES-256-GCM compartilhada usada para cifrar as mensagens da sessão.

---

## Stack tecnológica

### Backend
- **Python 3.11+**
- **FastAPI** — servidor HTTP + WebSocket assíncrono
- **uvicorn** — servidor ASGI
- **Qiskit Aer 0.13+** — simulação do canal quântico para BB84
- **liboqs-python** — implementação de referência do ML-KEM (FIPS 203)
- **PyCryptodome** — RSA e AES-256-GCM
- **cryptography** — HKDF, X.509, bcrypt
- **PyJWT** — tokens JWT para sessão HTTP
- **SQLAlchemy 2.0+** + **SQLite** (dev) / **PostgreSQL** (prod) — persistência apenas de usuários e logs (mensagens nunca são persistidas)
- **pydantic 2** — validação de dados
- **pytest** + **pytest-asyncio** + **coverage.py** — testes e cobertura
- **hypothesis** — testes baseados em propriedades para módulos criptográficos

### Frontend
- **Angular 17+** (standalone components)
- **TypeScript 5+**
- **RxJS** — reatividade
- **Angular Material** — componentes de UI
- **socket.io-client** ou **native WebSocket API** — comunicação tempo real
- **Karma + Jasmine** — testes unitários

### Comunicação
- **HTTPS (TLS 1.3)** para REST
- **WSS (WebSocket Secure)** para mensagens em tempo real
- **JSON** como formato de payload
- **Schemas Pydantic** sincronizados entre backend e frontend

### Infraestrutura
- **Docker** + **docker-compose** — empacotamento e orquestração local
- **Nginx** — reverse proxy + terminação TLS em produção
- **Let's Encrypt** — certificados em produção; **mkcert** em dev
- **Fly.io**, **Railway** ou **Hetzner VPS** — deploy público

### Qualidade e CI/CD
- **Git** + **GitHub** — versionamento
- **GitHub Actions** — CI: lint, testes, build
- **ruff** + **black** — lint + formatação Python
- **eslint** + **prettier** — lint + formatação TypeScript
- **pre-commit** — hooks locais

---

## Estrutura de diretórios

```
tcc-system/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point
│   │   ├── api/
│   │   │   ├── auth.py                # rotas de autenticação
│   │   │   ├── session.py             # rotas de sessão
│   │   │   └── websocket.py           # endpoint WSS
│   │   ├── core/
│   │   │   ├── config.py              # configuração via env
│   │   │   ├── security.py            # bcrypt, JWT
│   │   │   └── session_manager.py     # Singleton
│   │   ├── crypto/
│   │   │   ├── protocol_factory.py    # Factory
│   │   │   ├── key_protocol.py        # interface
│   │   │   ├── bb84/
│   │   │   │   ├── protocol.py        # pipeline completo
│   │   │   │   ├── sifting.py
│   │   │   │   ├── qber.py
│   │   │   │   ├── cascade.py
│   │   │   │   └── privacy_amp.py
│   │   │   ├── mlkem/protocol.py
│   │   │   ├── hybrid/
│   │   │   │   ├── protocol.py
│   │   │   │   └── combiner.py        # HKDF
│   │   │   ├── rsa/protocol.py
│   │   │   ├── message_cipher.py      # AES-256-GCM
│   │   │   └── eve_simulator.py       # passive/IR/BS
│   │   ├── monitor/
│   │   │   ├── qber_monitor.py        # Subject
│   │   │   └── observers.py           # Logger/Notification/Terminator
│   │   ├── models/                    # SQLAlchemy
│   │   └── schemas/                   # Pydantic
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── property/
│   ├── experiments/
│   │   ├── exp1_key_time.py
│   │   ├── exp2_qber.py
│   │   ├── exp3_throughput.py
│   │   └── exp4_robustness.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/                  # services, guards, interceptors
│   │   │   ├── features/
│   │   │   │   ├── auth/              # login/cadastro
│   │   │   │   ├── chat/              # tela de chat
│   │   │   │   └── settings/          # seleção de modo
│   │   │   └── shared/                # componentes reutilizáveis
│   │   └── environments/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── docker-compose.prod.yml
├── nginx/
│   └── nginx.conf
├── .github/workflows/ci.yml
└── README.md
```

---

## Features de desenvolvimento

Cada feature está vinculada aos requisitos funcionais (RF) e não funcionais (RNF) do Capítulo 3 do TCC.

---

### F1. Bootstrap e infraestrutura

**F1.1** Criar repositório Git público com licença MIT, README inicial, .gitignore, pre-commit hooks (ruff, black, eslint, prettier).

**F1.2** Configurar `pyproject.toml` no backend com dependências pinadas e ferramentas de qualidade.

**F1.3** Configurar projeto Angular 17 com standalone components e Angular Material.

**F1.4** Criar `docker-compose.yml` para subir backend + frontend + Postgres localmente com um comando.

**F1.5** Configurar GitHub Actions para rodar lint + testes + build em cada push.

**F1.6** Configurar variáveis de ambiente via `.env` (JWT secret, DB url, parâmetros do BB84).

---

### F2. Autenticação e gestão de usuários (RF01, RF02, RNF05)

**F2.1** Modelo `User` no SQLAlchemy: id (UUID), username (único), password_hash (bcrypt com cost 12), created_at.

**F2.2** Endpoint `POST /auth/register` com validação (username 3-32 caracteres alfanuméricos, senha mínimo 8 caracteres) e hash bcrypt.

**F2.3** Endpoint `POST /auth/login` retornando JWT (HS256, expiração 24h).

**F2.4** Middleware FastAPI para validar JWT em rotas protegidas.

**F2.5** Frontend: tela de cadastro com validação client-side espelhada.

**F2.6** Frontend: tela de login com armazenamento do JWT em `localStorage` e interceptor que adiciona o token nas requisições.

**F2.7** Guard Angular bloqueando rotas autenticadas sem token válido.

**F2.8** Endpoint `GET /auth/me` para validar token e retornar perfil.

---

### F3. Gestão de sessões (RF03, RF10)

**F3.1** Modelo `Session` em memória (não persistido): id, alice_id, bob_id, mode, key (bytes), state, created_at, qber.

**F3.2** Implementar `SessionManager` como Singleton em `core/session_manager.py` — gerencia dicionário de sessões ativas, com lock para concorrência.

**F3.3** Endpoint `POST /sessions/request` — Alice pede sessão com Bob no modo X; retorna `session_id` pendente.

**F3.4** Notificar Bob via WSS sobre solicitação pendente.

**F3.5** Endpoint `POST /sessions/{id}/accept` ou `/reject` para Bob.

**F3.6** Endpoint `DELETE /sessions/{id}` — encerra sessão, dispara descarte explícito da chave da memória (sobrescrita com zeros antes de liberar).

**F3.7** Timeout automático de sessões inativas após 30 minutos.

---

### F4. WebSocket e canal clássico (RNF04)

**F4.1** Endpoint `WSS /ws/{token}` com autenticação via JWT no path.

**F4.2** Protocolo de mensagens WSS estruturado em JSON: `{type, session_id, payload}` com tipos enumerados.

**F4.3** Pool de conexões WSS por usuário no `SessionManager`.

**F4.4** Heartbeat ping/pong a cada 30s para detectar desconexões.

**F4.5** Reconexão automática com backoff exponencial no cliente Angular.

**F4.6** TLS obrigatório em produção (nginx + Let's Encrypt); mkcert para dev local.

---

### F5. Interface comum de protocolo (RF04-RF07)

**F5.1** Definir `KeyEstablishmentProtocol` como classe abstrata em `crypto/key_protocol.py` com métodos `initiate()`, `respond(initiation_data)`, `get_key()`, `get_metrics()`.

**F5.2** Implementar `ProtocolFactory.create(mode: ProtocolMode) -> KeyEstablishmentProtocol`.

**F5.3** Enum `ProtocolMode`: BB84, MLKEM, HYBRID, RSA.

**F5.4** Estrutura de retorno `ProtocolMetrics`: tempo, qber (se aplicável), bytes trocados, tamanho da chave final.

---

### F6. Pipeline BB84 completo (RF04, RF09, RNF03)

**F6.1** Módulo `bb84/protocol.py`: Alice gera N bits aleatórios e N bases aleatórias usando `secrets`. N parametrizado por configuração (default 4096 para chave final de 256 bits após reconciliação e amplificação).

**F6.2** Codificação dos qubits em Qiskit Aer: estados |0⟩, |1⟩ na base Z; |+⟩, |-⟩ na base X.

**F6.3** Transmissão simulada do circuito quântico pelo `EveSimulator` (modo `passive` quando sem Eve).

**F6.4** Medição por Bob em bases aleatórias com Qiskit Aer (`shots=1`).

**F6.5** `bb84/sifting.py`: troca de bases pelo canal clássico WSS; retém bits onde as bases coincidem.

**F6.6** `bb84/qber.py`: reserva e revela 25% da chave sifted como amostra; calcula QBER como fração de discrepâncias.

**F6.7** Limiar de QBER configurável (default 15%); acima disso, sessão é abortada com evento `eve_detected` propagado via Observer.

**F6.8** `bb84/cascade.py`: implementação do protocolo Cascade com 4 passes; tamanho de bloco inicial calculado em função do QBER estimado conforme Brassard & Salvail (1993).

**F6.9** `bb84/privacy_amp.py`: hashing universal por matriz de Toeplitz aleatória; comprimento da chave final calculado pela fórmula de Shor-Preskill `ℓ = n·[1 − 2·h₂(Q)]`.

**F6.10** Saída final: chave de 256 bits para AES-GCM.

---

### F7. Integração ML-KEM (RF05)

**F7.1** Módulo `mlkem/protocol.py` usando `liboqs-python`.

**F7.2** Selecionar nível de segurança ML-KEM-768 (NIST Level 3, equivalente a AES-192) como default. Parametrizável.

**F7.3** Fluxo: Bob gera (pk, sk) com `KeyEncapsulation('ML-KEM-768').generate_keypair()`; envia pk via WSS.

**F7.4** Alice executa `encap_secret(pk)` retornando (ct, K); envia ct via WSS.

**F7.5** Bob executa `decap_secret(ct)` recuperando K.

**F7.6** Validação de tamanhos esperados: pk = 1184 bytes, ct = 1088 bytes, K = 32 bytes (ML-KEM-768).

**F7.7** Tratamento de falha de decapsulamento (chave inválida → aborta sessão).

---

### F8. Combinador Híbrido (RF06)

**F8.1** Módulo `hybrid/combiner.py`: implementação de HKDF-SHA256 conforme RFC 5869.

**F8.2** Construção: `K_final = HKDF(salt=nonce_aleatorio_32B, ikm=K_bb84 || K_mlkem, info="qchat-hybrid-v1", length=32)`.

**F8.3** Salt gerado por `secrets.token_bytes(32)` e trocado entre Alice e Bob via canal autenticado.

**F8.4** Módulo `hybrid/protocol.py`: executa BB84 e ML-KEM em paralelo via `asyncio.gather`, depois combina.

**F8.5** Se um dos protocolos componentes falhar, registrar evento e continuar com a chave do componente sobrevivente (validação do Experimento 4 do TCC).

---

### F9. RSA como controle (RF07)

**F9.1** Módulo `rsa/protocol.py` com `PyCryptodome`; chave de 2048 bits.

**F9.2** Bob gera par e envia chave pública via WSS.

**F9.3** Alice gera chave de sessão de 32 bytes via `secrets`, cifra com RSA-OAEP (SHA-256), envia ciphertext.

**F9.4** Bob decifra recuperando a chave.

---

### F10. Cifragem simétrica de mensagens (RF08, RNF03)

**F10.1** Módulo `crypto/message_cipher.py`: AES-256-GCM via `PyCryptodome`.

**F10.2** Nonce de 96 bits gerado por `secrets` para cada mensagem, transmitido junto com o ciphertext.

**F10.3** Associated data: timestamp + session_id + sequence_number (proteção contra replay).

**F10.4** Tag de autenticação de 128 bits; falha de verificação → mensagem descartada e evento registrado.

**F10.5** Sequence number incremental por sessão para detectar mensagens fora de ordem ou repetidas.

---

### F11. Modelo de adversário simulado (RF09, validação experimental)

**F11.1** Módulo `crypto/eve_simulator.py` com modos: `PASSIVE`, `INTERCEPT_RESEND`, `BEAM_SPLITTING(fraction)`.

**F11.2** `INTERCEPT_RESEND`: para cada qubit, Eve escolhe base aleatória, mede, reenvia o estado medido.

**F11.3** `BEAM_SPLITTING`: Eve mantém cópia de uma fração `f` dos qubits sem perturbar os demais (no modelo simulado isso é representado retendo info para análise posterior).

**F11.4** Eve é ativada apenas via flag de configuração (`EVE_MODE=...`) — nunca em produção.

**F11.5** Logs de Eve em arquivo separado para análise dos experimentos.

---

### F12. Monitor de QBER e Observer pattern (RF09, RF11, RF12)

**F12.1** `monitor/qber_monitor.py`: classe `QBERMonitor` com lista de observers, threshold configurável, método `update_qber(value, session_id)`.

**F12.2** `monitor/observers.py`:
- `Logger` — registra evento estruturado em JSON.
- `NotificationService` — envia mensagem WSS para o frontend com tipo `qber_alert`.
- `SessionTerminator` — chama `SessionManager.close_session(id, reason='eve_detected')` se QBER > threshold.

**F12.3** Cada observer implementa interface `Observer.on_event(event: dict)`.

---

### F13. Logging estruturado (RF11)

**F13.1** Logger configurado com `structlog` ou `logging` + `python-json-logger`.

**F13.2** Eventos registrados: `session_created`, `key_established`, `qber_measured`, `eve_detected`, `message_sent`, `message_received`, `session_closed`.

**F13.3** Cada evento inclui: timestamp ISO 8601, session_id, mode, métricas relevantes.

**F13.4** Logs em arquivo rotativo (5 MB por arquivo, 10 arquivos) e em stdout em dev.

**F13.5** Endpoint admin `GET /logs/export?session_id=X` retorna CSV para análise dos experimentos.

---

### F14. Frontend — telas principais

**F14.1** Tela de cadastro (`/register`): formulário com validação reativa.

**F14.2** Tela de login (`/login`): formulário com tratamento de erro.

**F14.3** Tela de lobby (`/lobby`): lista de usuários online, botão para iniciar sessão com seleção de modo.

**F14.4** Tela de chat (`/chat/:sessionId`): exibe mensagens em ordem cronológica; campo de input; indicador de digitação; status de conexão.

**F14.5** Indicador visual de QBER e do modo da sessão sempre visíveis na tela de chat.

**F14.6** Modal de alerta de espionagem quando QBER > threshold, com opção de encerrar.

**F14.7** Tela de configurações (`/settings`): parâmetros visíveis (N de qubits, threshold de QBER, nível ML-KEM) — apenas leitura para usuário comum.

---

### F15. Camada de comunicação no frontend (MVC)

**F15.1** Service Angular `AuthService` — login, logout, refresh do token.

**F15.2** Service Angular `SessionService` — criar/aceitar/encerrar sessões.

**F15.3** Service Angular `WebSocketService` — conexão WSS, reconexão automática, observable de mensagens.

**F15.4** Service Angular `CryptoMetricsService` — recebe e expõe métricas de QBER, status da sessão.

**F15.5** State management leve com signals do Angular 17 (sem necessidade de NgRx).

---

### F16. Testes automatizados (RNF07)

**F16.1** **Unitários — BB84**: gerar qubits, sifting, QBER (com Eve em IR esperar ~25%), Cascade (corrigir taxa de erro definida), privacy amplification (entropy check).

**F16.2** **Unitários — ML-KEM**: keygen, encaps, decaps, validação de tamanhos.

**F16.3** **Unitários — Hybrid**: HKDF determinístico para mesmas entradas.

**F16.4** **Unitários — AES-GCM**: ciclo encrypt/decrypt; falha de tag.

**F16.5** **Unitários — RSA**: keygen, exchange, decrypt.

**F16.6** **Property-based (hypothesis)**:
- BB84: ∀ entrada, sem Eve → QBER < 1%.
- BB84 com IR: ∀ entrada, QBER ∈ [20%, 30%].
- Privacy amp: ∀ chave reconciliada, tamanho final = ⌊n·(1−2h₂(Q))⌋.
- HKDF: ∀ (k1, k2), comprimento de saída = especificado.

**F16.7** **Integração**: sessão BB84 completa fim-a-fim entre dois clientes mock; sessão ML-KEM; sessão Híbrida; sessão Híbrida com falha simulada de um componente.

**F16.8** **Sistema (E2E)**: Playwright para cadastro + login + iniciar sessão + trocar mensagens nos 4 modos.

**F16.9** Cobertura mínima de 85% nos módulos `crypto/` e `monitor/` reportada via `coverage.py`.

**F16.10** CI bloqueia merge se cobertura cair abaixo do limiar.

---

### F17. Scripts de experimento (alimentam Cap. 4 do TCC)

**F17.1** `experiments/exp1_key_time.py`: rodada de 30 execuções para cada combinação (modo × tamanho_chave). Saída CSV: `mode, key_size, time_ms, run`.

**F17.2** `experiments/exp2_qber.py`: 30 execuções para cada modo de Eve (none, IR_total, BS_10, BS_25, BS_50). Saída CSV: `eve_mode, qber, threshold_exceeded, run`.

**F17.3** `experiments/exp3_throughput.py`: para chave já estabelecida, enviar 1000 mensagens de tamanhos {100B, 1KB, 10KB}. Saída CSV: `msg_size, latency_ms, throughput_msgs_s`.

**F17.4** `experiments/exp4_robustness.py`: forçar comprometimento de cada componente e medir comportamento do híbrido. Saída CSV: `scenario, key_established, key_entropy`.

**F17.5** `experiments/plot.py`: gera gráficos publicáveis (matplotlib) a partir dos CSVs — barras com erro, linhas, boxplots — exportando PDF vetorial.

**F17.6** `experiments/stats.py`: estatística descritiva e teste t para comparações entre modos.

**F17.7** Execução: `make experiments` roda os 4 scripts e gera todos os gráficos automaticamente.

---

### F18. Deploy (RNF08)

**F18.1** `Dockerfile` do backend: multi-stage (build → runtime), usuário não-root, imagem base `python:3.11-slim`.

**F18.2** `Dockerfile` do frontend: multi-stage (build com node → serve estático com nginx).

**F18.3** `docker-compose.prod.yml` com nginx reverse proxy, terminação TLS, redes isoladas.

**F18.4** Deploy em VPS (Hetzner CX22, ~€5/mês) ou Fly.io free tier.

**F18.5** Domínio próprio com Let's Encrypt via certbot.

**F18.6** Documentação em `DEPLOY.md` com passos exatos para que a banca consiga subir uma instância local em até 5 minutos com `docker-compose up`.

**F18.7** Health checks: `GET /health` no backend; `/healthz` no nginx.

---

### F19. Documentação

**F19.1** `README.md` principal com badges (CI, cobertura, licença), descrição do projeto, link para o TCC em PDF, link para a aplicação em produção, instruções de uso local.

**F19.2** `backend/README.md` com instruções de desenvolvimento.

**F19.3** `frontend/README.md` com instruções de desenvolvimento.

**F19.4** `ARCHITECTURE.md` com diagrama de componentes e decisões técnicas.

**F19.5** `EXPERIMENTS.md` documentando como reproduzir os 4 experimentos.

**F19.6** Documentação OpenAPI automática via FastAPI em `/docs`.

**F19.7** `CHANGELOG.md` no formato Keep a Changelog.

**F19.8** `LICENSE` (MIT).

---

## Ordem de execução recomendada

1. **F1** — infraestrutura básica do repositório
2. **F2** + **F3** — autenticação e sessões (esqueleto sem cripto)
3. **F4** — canal WSS funcionando
4. **F5** — interface comum + factory
5. **F9** — RSA primeiro (mais simples, valida o pipeline ponta-a-ponta)
6. **F10** — AES-GCM para cifrar mensagens com a chave do RSA
7. **F14** + **F15** — frontend básico funcionando com RSA
8. **F7** — ML-KEM
9. **F6** — BB84 completo (mais complexo, deixar por último entre os protocolos)
10. **F8** — combinador híbrido
11. **F11** + **F12** + **F13** — Eve e observabilidade
12. **F16** — testes em paralelo com cada feature
13. **F17** — scripts de experimento após tudo funcionando
14. **F18** — deploy
15. **F19** — documentação ao longo de todo o processo

---

## Cobertura dos requisitos do TCC

| Requisito | Features que cobrem |
|---|---|
| RF01 | F2.1, F2.2, F2.5 |
| RF02 | F2.3, F2.4, F2.6 |
| RF03 | F3.3, F3.4, F3.5 |
| RF04 | F5, F6 |
| RF05 | F5, F7 |
| RF06 | F5, F8 |
| RF07 | F5, F9 |
| RF08 | F10 |
| RF09 | F6.7, F11, F12 |
| RF10 | F3.6 |
| RF11 | F13 |
| RF12 | F12.2 |
| RNF01, RNF02 | F17.1, F17.3 (validação) |
| RNF03 | F6.9, F8.2, F10.1 |
| RNF04 | F4 |
| RNF05 | F2.1 (bcrypt) |
| RNF06 | F14, F15 |
| RNF07 | F16.9, F16.10 |
| RNF08 | F18 |
