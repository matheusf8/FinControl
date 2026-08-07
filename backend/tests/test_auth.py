"""Testes de autenticação: registro, login, refresh, rota protegida."""


def test_register_creates_user(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "ana@example.com", "password": "senha1234", "full_name": "Ana"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "ana@example.com"
    assert body["full_name"] == "Ana"
    assert "password" not in body
    assert "hashed_password" not in body  # nunca vaza a senha (nem o hash) na resposta


def test_register_duplicate_email_fails(client):
    payload = {"email": "dup@example.com", "password": "senha1234"}
    client.post("/api/auth/register", json=payload)
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409


def test_register_short_password_fails_validation(client):
    resp = client.post(
        "/api/auth/register", json={"email": "curta@example.com", "password": "123"}
    )
    assert resp.status_code == 422


def test_login_with_correct_password(client):
    client.post("/api/auth/register", json={"email": "login@example.com", "password": "senha1234"})
    resp = client.post(
        "/api/auth/login", json={"email": "login@example.com", "password": "senha1234"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_with_wrong_password_fails(client):
    client.post("/api/auth/register", json={"email": "wrong@example.com", "password": "senha1234"})
    resp = client.post(
        "/api/auth/login", json={"email": "wrong@example.com", "password": "errada123"}
    )
    assert resp.status_code == 401


def test_login_with_unknown_email_fails(client):
    resp = client.post(
        "/api/auth/login", json={"email": "naoexiste@example.com", "password": "senha1234"}
    )
    assert resp.status_code == 401


def test_me_requires_authentication(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_valid_token(client):
    client.post(
        "/api/auth/register",
        json={"email": "me@example.com", "password": "senha1234", "full_name": "Eu"},
    )
    login_resp = client.post(
        "/api/auth/login", json={"email": "me@example.com", "password": "senha1234"}
    )
    token = login_resp.json()["access_token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_me_with_garbage_token_fails(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer token-invalido"})
    assert resp.status_code == 401


def test_refresh_token_issues_new_access_token(client):
    client.post("/api/auth/register", json={"email": "refresh@example.com", "password": "senha1234"})
    login_resp = client.post(
        "/api/auth/login", json={"email": "refresh@example.com", "password": "senha1234"}
    )
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_refresh_with_access_token_fails(client):
    """Um access token não pode ser usado como refresh token (tipos diferentes)."""
    client.post("/api/auth/register", json={"email": "wrongtype@example.com", "password": "senha1234"})
    login_resp = client.post(
        "/api/auth/login", json={"email": "wrongtype@example.com", "password": "senha1234"}
    )
    access_token = login_resp.json()["access_token"]

    resp = client.post("/api/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
