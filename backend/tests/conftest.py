"""Fixtures compartilhadas: banco de teste isolado (SQLite em memória, nunca
toca no fincontrol.db real de desenvolvimento)."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — garante que todos os models registram em Base.metadata
from app.core import rate_limit
from app.core.database import Base, get_db
from app.main import app as fastapi_app


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    """O rate limiter guarda estado em dicts a nível de módulo (propositalmente,
    é em memória mesmo em produção — ver app/core/rate_limit.py). Sem resetar
    entre testes, o TestClient sempre bate com o mesmo "IP", e testes que
    registram/logam repetidamente acabariam se travando uns aos outros."""
    rate_limit._attempts.clear()
    rate_limit._locked_until.clear()
    yield
    rate_limit._attempts.clear()
    rate_limit._locked_until.clear()


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = testing_session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Registra e loga um usuário, retorna os headers já com o Bearer token
    (a maioria dos testes de contas/categorias/transações precisa disso)."""
    client.post(
        "/api/auth/register",
        json={"email": "fixture@example.com", "password": "senha1234", "full_name": "Fixture"},
    )
    login_resp = client.post(
        "/api/auth/login", json={"email": "fixture@example.com", "password": "senha1234"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
