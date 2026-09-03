"""Configuracao da aplicacao carregada de variaveis de ambiente / .env."""

from functools import lru_cache

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_JWT_SECRET = "dev-insecure-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Aplicacao
    app_name: str = "QChat"
    environment: str = "development"
    debug: bool = True

    # Seguranca / JWT
    jwt_secret: str = _DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    bcrypt_cost: int = 12

    # Banco de dados
    database_url: str = "sqlite:///./qchat.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:4200"]

    # Sessao
    session_timeout_minutes: int = 30

    # BB84
    bb84_qubits: int = 4096
    qber_threshold: float = 0.15
    cascade_passes: int = 4

    # ML-KEM
    mlkem_level: str = "ML-KEM-768"

    # Adversario simulado — NUNCA ativo em producao
    eve_mode: str = "PASSIVE"
    eve_beam_split_fraction: float = 0.1

    # WebSocket
    ws_heartbeat_seconds: int = 30

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @model_validator(mode="after")
    def _guard_production_settings(self) -> "Settings":
        """Impede a inicializacao em producao com configuracoes inseguras."""
        if self.is_production:
            if self.jwt_secret == _DEFAULT_JWT_SECRET or len(self.jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET inseguro em producao: defina a variavel de ambiente "
                    "JWT_SECRET com um segredo aleatorio de pelo menos 32 caracteres."
                )
            if self.eve_mode.upper() != "PASSIVE":
                raise ValueError(
                    "EVE_MODE deve ser PASSIVE em producao; o adversario simulado "
                    "nunca deve compor o sistema em operacao real."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
