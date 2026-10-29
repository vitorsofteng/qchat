# QChat: Hybrid Quantum-Resistant Messaging System

[![CI](https://github.com/vitorsofteng/qchat/actions/workflows/ci.yml/badge.svg)](https://github.com/vitorsofteng/qchat/actions/workflows/ci.yml)
![Coverage](https://img.shields.io/badge/crypto%20coverage-%E2%89%A585%25-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

Proof-of-concept one-to-one messaging system with ephemeral messages and four
selectable key-establishment modes:

| Mode | Description |
|---|---|
| **BB84** | Quantum Key Distribution (QKD), full pipeline: sifting, QBER estimation, Cascade reconciliation and Toeplitz privacy amplification |
| **ML-KEM** | Post-Quantum Cryptography (PQC), NIST FIPS 203 (ML-KEM-768) |
| **Hybrid** | BB84 + ML-KEM combined through HKDF |
| **RSA** | Classical cryptography, used as experimental control |

Every mode produces an AES-256-GCM key that encrypts the messages of the session.
The quantum channel is simulated with Qiskit Aer, and a simulated eavesdropper
(Eve) can run intercept-resend and beam-splitting attacks.

This repository is the experimental artifact of my undergraduate thesis in
Software Engineering at the University of Brasília (UnB), Brazil, 2026:
*Development of a Secure Chat with a Hybrid Scheme of Quantum Key Distribution
(QKD) and Post-Quantum Cryptography (PQC)*.

## Main results

Four controlled experiments, 30 replications per configuration
(1000 messages per size in experiment 3):

| Experiment | Result |
|---|---|
| Key-establishment time | ML-KEM: about 2 ms. Hybrid: 285 ms, not statistically different from BB84 alone with 1024 qubits (Welch's t-test, p = 0.61). RSA-2048: 917 ms |
| QBER under attack | Intercept-resend raised the QBER to 25.2% on average and was detected in 30/30 runs (threshold 15%). Beam-splitting, in the simplified form simulated, left the QBER at 0% |
| Message throughput | AES-256-GCM latency below 1 ms for 100 B, 1 kB and 10 kB messages |
| Hybrid robustness | The hybrid mode kept establishing keys when one of its two components failed, and aborted only when both failed |

## Known limitations

These are discussed in the thesis and motivate the next steps of this research:

- The quantum channel is ideal and noiseless, and the final key length uses the
  asymptotic Shor-Preskill bound without finite-key corrections.
- Beam-splitting is modelled only by its effect on the QBER, without photon-number
  statistics or channel loss, so decoy-state detection is not evaluated.
- The server runs the key-establishment protocols and therefore knows the session
  key. The system protects messages against network observers, but it is not
  end-to-end encrypted in the sense of the Signal Protocol.
- The robustness experiment measures availability after a detected failure, not
  security when a component is silently broken.

## Stack

- **Backend:** Python 3.11, FastAPI, Qiskit Aer, liboqs-python, PyCryptodome, cryptography
- **Frontend:** Angular 21 (standalone + signals), Angular Material
- **Communication:** HTTPS/WSS, JSON
- **Infrastructure:** Docker, nginx, GitHub Actions

## Running locally

### Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev,quantum]"                  # base + all 4 modes
uvicorn app.main:app --port 8000
```

On Linux or macOS, activate the environment with `source .venv/bin/activate`.

### Frontend

```bash
cd frontend
npm install
npm start
```

Application at **http://localhost:4200** · API at http://localhost:8000 ·
interactive API docs at http://localhost:8000/docs

Detailed steps, including Docker and production, are in [DEPLOY.md](DEPLOY.md).

## Structure

```
backend/      FastAPI API, cryptographic protocols, experiments
frontend/     Angular application
nginx/        production reverse proxy
docs/         feature specifications and thesis documents
```

## Documentation

The documents below are written in Portuguese.

- [Architecture](ARCHITECTURE.md): components and technical decisions
- [Deployment](DEPLOY.md): local and production setup
- [Experiments](EXPERIMENTS.md): how to reproduce the 4 experiments
- [Changelog](CHANGELOG.md)
- [Backend](backend/README.md) · [Frontend](frontend/README.md)

## Tests

```bash
cd backend && pytest          # backend test suite (coverage ≥ 85% in crypto/)
cd frontend && npm run lint   # frontend lint
```

## Author

Vitor Eduardo Kühl Rodrigues · vitor.softeng@gmail.com

## License

[MIT](LICENSE)
