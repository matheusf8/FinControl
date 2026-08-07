"""Configurações da aplicação, lidas de variáveis de ambiente (.env)."""
import os
import secrets
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _app_dir() -> Path:
    """Pasta onde ficam os dados graváveis (fincontrol.db, .env).

    Empacotado (PyInstaller): __file__ aponta pra dentro da pasta interna
    extraída do bundle, não pra onde o FinControl.exe realmente está — usar
    isso pro banco de dados quebraria a portabilidade (copiar a pasta pra
    outro PC/pen drive perderia os dados, que ficariam presos dentro do
    bundle). `sys.executable` é o caminho do próprio .exe nesse caso.

    Em desenvolvimento: sys.executable é o python.exe do venv, não o que
    queremos — aí sim usamos __file__ pra achar a raiz de backend/.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent.parent


BASE_DIR = _app_dir()


def _ensure_env_file() -> None:
    """App pessoal empacotado não tem terminal pra rodar `secrets.token_hex`
    nem editor pra colar num .env — então, se ninguém configurou uma
    SECRET_KEY (nem variável de ambiente, nem .env já existente), gera uma
    aleatória forte na primeira execução e grava um .env local ao lado do
    banco. Fica única por instalação, sem exigir nenhum passo manual.

    Pulado durante os testes (pytest) de propósito, pra não escrever um .env
    de verdade no disco como efeito colateral de rodar a suite.
    """
    if "pytest" in sys.modules:
        return
    if os.environ.get("SECRET_KEY"):
        return
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        return
    env_path.write_text(f"SECRET_KEY={secrets.token_hex(32)}\n", encoding="utf-8")


_ensure_env_file()


class Settings(BaseSettings):
    app_name: str = "FinControl"

    # Banco de dados: arquivo SQLite ao lado do .exe (ou de backend/ em dev)
    database_url: str = f"sqlite:///{BASE_DIR / 'fincontrol.db'}"

    # JWT
    secret_key: str = "change-me-in-.env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
