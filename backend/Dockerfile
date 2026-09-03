# QChat backend — imagem multi-stage com os 4 modos criptograficos (F18.1).
#
# Os extras `quantum` (qiskit-aer, liboqs-python) sao incluidos. O liboqs e
# compilado durante o build da imagem; as ferramentas de compilacao permanecem
# no runtime como fallback. Imagem grande (~1,3 GB) — aceitavel para o artefato
# de TCC. O build leva varios minutos.

FROM python:3.11-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git ninja-build \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
RUN pip install --no-cache-dir --upgrade pip
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --no-cache-dir --target=/install ".[quantum]"

FROM python:3.11-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake git \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/deps \
    HOME=/home/qchat
WORKDIR /app

RUN useradd --create-home --uid 1000 qchat
COPY --from=build /install /app/deps
COPY app ./app

# Pre-compila o liboqs na imagem para evitar a compilacao na primeira requisicao.
RUN su qchat -c "python -c 'import oqs'" || true
RUN chown -R qchat:qchat /home/qchat

USER qchat
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
