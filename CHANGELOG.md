# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e o projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### A fazer
- Testes E2E com Playwright (F16.8)
- Implantação em URL pública (F18.4, F18.5)

## [0.1.0] — 2026-05-22

### Adicionado
- Infraestrutura do repositório, `docker-compose`, CI (GitHub Actions)
- Autenticação de usuários com bcrypt e JWT
- Gestão de sessões em memória com `SessionManager` (Singleton)
- Canal WebSocket com heartbeat e reconexão
- Interface comum de protocolo (`KeyEstablishmentProtocol`) e `ProtocolFactory`
- Protocolo **RSA-2048** (controle experimental)
- Protocolo **ML-KEM** (NIST FIPS 203, via liboqs)
- Pipeline **BB84** completo: sifting, estimativa de QBER, reconciliação
  Cascade e amplificação de privacidade
- Combinador **Híbrido** BB84 + ML-KEM via HKDF
- Cifragem de mensagens AES-256-GCM
- Adversário simulado (`EveSimulator`): passivo, intercept-resend, beam-splitting
- Monitor de QBER com padrão Observer e detecção de espionagem
- Logging estruturado em JSON e exportação de logs em CSV
- Frontend Angular: telas de login, cadastro, lobby, chat e configurações
- Scripts dos quatro experimentos com geração de gráficos e estatística
- Suíte de testes (unitários, integração, property-based) com cobertura ≥ 85%
