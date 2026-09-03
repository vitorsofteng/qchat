"""Configuracao compartilhada de testes."""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_qchat.db")
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production")
os.environ.setdefault("ENVIRONMENT", "test")
# Menos qubits nos testes: BB84 com 4096 qubits deixaria a suite lenta.
os.environ.setdefault("BB84_QUBITS", "1024")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402,F401 -- registra modelos na metadata
from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """TestClient com banco limpo por teste."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
