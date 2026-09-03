# QChat — Frontend

Aplicação Angular do sistema de chat híbrido QKD+PQC.

## Requisitos

- Node.js 20+ e npm

## Desenvolvimento

```bash
npm install
npm start          # servidor de dev em http://localhost:4200
```

Em `localhost`, a aplicação aponta para o backend de desenvolvimento em
`http://localhost:8000`. O backend precisa estar rodando — ver
[guia de implantação](../DEPLOY.md).

## Scripts

```bash
npm run build      # build de produção em dist/
npm run lint       # ESLint
npm test           # testes unitários
```

## Estrutura

```
src/app/
  core/
    models/         interfaces (sessão, usuário, mensagens WS)
    services/       Auth, Session, WebSocket, CryptoMetrics, MessageCrypto, User
    guards/         guard de rota autenticada
    interceptors/   injeção do token JWT
  features/         telas: auth, lobby, chat, settings
  shared/           toolbar e modal de alerta de QBER
```

As mensagens são cifradas no cliente com AES-256-GCM (Web Crypto API), usando a
chave de sessão estabelecida pelo backend.
