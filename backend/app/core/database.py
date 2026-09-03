"""Configuracao do banco de dados (SQLAlchemy 2.0)."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_connect_args: dict = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos ORM."""


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: fornece uma sessao de banco por requisicao."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Cria as tabelas. Em producao seria substituido por migracoes (Alembic)."""
    from app import models  # noqa: F401 -- garante o registro dos modelos

    Base.metadata.create_all(bind=engine)
