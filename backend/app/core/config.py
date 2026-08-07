"""Configurações da aplicação, lidas de variáveis de ambiente (.env)."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "FinControl"

    # Banco de dados: arquivo SQLite dentro da pasta backend/, ao lado do .exe quando empacotado
    database_url: str = f"sqlite:///{BASE_DIR / 'fincontrol.db'}"

    # JWT
    secret_key: str = "change-me-in-.env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
