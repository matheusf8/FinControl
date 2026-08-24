"""Testes de autenticação: registro, login, refresh, rota protegida."""
from app.core import rate_limit
from app.core.config import settings
from app.models.user import User
from app.services.email_service import EmailSendError


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


def test_me_defaults_cycle_closing_day_to_24(client):
    client.post("/api/auth/register", json={"email": "ciclo@example.com", "password": "senha1234"})
    login_resp = client.post(
        "/api/auth/login", json={"email": "ciclo@example.com", "password": "senha1234"}
    )
    token = login_resp.json()["access_token"]

    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.json()["cycle_closing_day"] == 24


def test_update_cycle_closing_day(client):
    client.post("/api/auth/register", json={"email": "ciclo2@example.com", "password": "senha1234"})
    login_resp = client.post(
        "/api/auth/login", json={"email": "ciclo2@example.com", "password": "senha1234"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    resp = client.patch("/api/auth/me", json={"cycle_closing_day": 15}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["cycle_closing_day"] == 15

    # persiste — uma consulta separada em /me reflete o valor salvo
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.json()["cycle_closing_day"] == 15


def test_update_cycle_closing_day_rejects_out_of_range(client):
    client.post("/api/auth/register", json={"email": "ciclo3@example.com", "password": "senha1234"})
    login_resp = client.post(
        "/api/auth/login", json={"email": "ciclo3@example.com", "password": "senha1234"}
    )
    headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    resp = client.patch("/api/auth/me", json={"cycle_closing_day": 0}, headers=headers)
    assert resp.status_code == 422
    resp = client.patch("/api/auth/me", json={"cycle_closing_day": 32}, headers=headers)
    assert resp.status_code == 422


def test_update_cycle_closing_day_requires_authentication(client):
    resp = client.patch("/api/auth/me", json={"cycle_closing_day": 15})
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


def test_login_locks_after_too_many_failed_attempts(client):
    """Rate limit básico: 5 tentativas erradas bloqueia o e-mail por um tempo,
    mesmo que a próxima tentativa use a senha certa."""
    email = "bruteforce@example.com"
    rate_limit.register_success(email)  # garante estado limpo se outro teste usou o mesmo módulo
    client.post("/api/auth/register", json={"email": email, "password": "senhaCorreta123"})

    for _ in range(rate_limit.MAX_ATTEMPTS):
        resp = client.post("/api/auth/login", json={"email": email, "password": "senhaErrada"})
        assert resp.status_code == 401

    resp = client.post("/api/auth/login", json={"email": email, "password": "senhaErrada"})
    assert resp.status_code == 429

    # bloqueado mesmo com a senha certa
    resp = client.post("/api/auth/login", json={"email": email, "password": "senhaCorreta123"})
    assert resp.status_code == 429

    rate_limit.register_success(email)  # limpa pro resto da suite


def test_login_rate_limit_is_per_email(client):
    """Tentativas erradas num e-mail não bloqueiam outro e-mail diferente."""
    email_a = "vitima-a@example.com"
    email_b = "vitima-b@example.com"
    client.post("/api/auth/register", json={"email": email_a, "password": "senhaCorreta123"})
    client.post("/api/auth/register", json={"email": email_b, "password": "senhaCorreta123"})

    for _ in range(rate_limit.MAX_ATTEMPTS):
        client.post("/api/auth/login", json={"email": email_a, "password": "senhaErrada"})

    resp = client.post("/api/auth/login", json={"email": email_b, "password": "senhaCorreta123"})
    assert resp.status_code == 200

    rate_limit.register_success(email_a)


def test_register_requires_invite_code_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "invite_code", "convite123")
    resp = client.post(
        "/api/auth/register",
        json={"email": "semcodigo@example.com", "password": "senha1234"},
    )
    assert resp.status_code == 403


def test_register_with_wrong_invite_code_fails(client, monkeypatch):
    monkeypatch.setattr(settings, "invite_code", "convite123")
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "codigoerrado@example.com",
            "password": "senha1234",
            "invite_code": "chuta123",
        },
    )
    assert resp.status_code == 403


def test_register_with_correct_invite_code_succeeds(client, monkeypatch):
    monkeypatch.setattr(settings, "invite_code", "convite123")
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "comcodigo@example.com",
            "password": "senha1234",
            "invite_code": "convite123",
        },
    )
    assert resp.status_code == 201


def _capture_sent_emails(monkeypatch) -> list[dict]:
    """Substitui o envio real (Resend) por uma lista em memória, pra pegar o
    link de redefinição sem precisar de RESEND_API_KEY nem chamar a internet
    de dentro do teste."""
    sent: list[dict] = []

    def fake_send_email(*, to: str, subject: str, html: str) -> None:
        sent.append({"to": to, "subject": subject, "html": html})

    monkeypatch.setattr("app.services.auth_service.send_email", fake_send_email)
    return sent


def test_forgot_password_sends_email_with_reset_link(client, monkeypatch):
    sent = _capture_sent_emails(monkeypatch)
    client.post(
        "/api/auth/register", json={"email": "recupera@example.com", "password": "senhaAntiga1"}
    )

    resp = client.post(
        "/api/auth/forgot-password",
        json={"email": "recupera@example.com", "reset_url_base": "https://app.exemplo.com"},
    )

    assert resp.status_code == 204
    assert len(sent) == 1
    assert sent[0]["to"] == "recupera@example.com"
    assert "https://app.exemplo.com/reset-password?token=" in sent[0]["html"]


def test_forgot_password_unknown_email_does_not_leak_and_sends_nothing(client, monkeypatch):
    sent = _capture_sent_emails(monkeypatch)
    resp = client.post(
        "/api/auth/forgot-password",
        json={"email": "naoexiste@example.com", "reset_url_base": "https://app.exemplo.com"},
    )
    # Sempre 204, exista ou não o e-mail — não pode dar pra descobrir por
    # aqui quais e-mails têm conta.
    assert resp.status_code == 204
    assert sent == []


def _extract_token(html: str) -> str:
    return html.split("token=")[1].split('"')[0]


def test_reset_password_with_valid_token_changes_password(client, monkeypatch):
    sent = _capture_sent_emails(monkeypatch)
    client.post(
        "/api/auth/register", json={"email": "trocasenha@example.com", "password": "senhaAntiga1"}
    )
    client.post(
        "/api/auth/forgot-password",
        json={"email": "trocasenha@example.com", "reset_url_base": "https://app.exemplo.com"},
    )
    token = _extract_token(sent[0]["html"])

    resp = client.post(
        "/api/auth/reset-password", json={"token": token, "new_password": "senhaNova123"}
    )
    assert resp.status_code == 204

    # senha antiga não funciona mais, a nova sim
    old = client.post(
        "/api/auth/login", json={"email": "trocasenha@example.com", "password": "senhaAntiga1"}
    )
    assert old.status_code == 401
    new = client.post(
        "/api/auth/login", json={"email": "trocasenha@example.com", "password": "senhaNova123"}
    )
    assert new.status_code == 200


def test_reset_password_token_is_single_use(client, monkeypatch):
    sent = _capture_sent_emails(monkeypatch)
    client.post(
        "/api/auth/register", json={"email": "usounico@example.com", "password": "senhaAntiga1"}
    )
    client.post(
        "/api/auth/forgot-password",
        json={"email": "usounico@example.com", "reset_url_base": "https://app.exemplo.com"},
    )
    token = _extract_token(sent[0]["html"])

    first = client.post(
        "/api/auth/reset-password", json={"token": token, "new_password": "senhaNova123"}
    )
    assert first.status_code == 204

    second = client.post(
        "/api/auth/reset-password", json={"token": token, "new_password": "outraSenha456"}
    )
    assert second.status_code == 400


def test_reset_password_with_bogus_token_fails(client):
    resp = client.post(
        "/api/auth/reset-password", json={"token": "token-invalido", "new_password": "senhaNova123"}
    )
    assert resp.status_code == 400


def test_reset_password_with_expired_token_fails(client, monkeypatch, db_session):
    from datetime import datetime, timedelta, timezone

    sent = _capture_sent_emails(monkeypatch)
    client.post(
        "/api/auth/register", json={"email": "expirado@example.com", "password": "senhaAntiga1"}
    )
    client.post(
        "/api/auth/forgot-password",
        json={"email": "expirado@example.com", "reset_url_base": "https://app.exemplo.com"},
    )
    token = _extract_token(sent[0]["html"])

    user = db_session.query(User).filter(User.email == "expirado@example.com").first()
    user.reset_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    db_session.commit()

    resp = client.post(
        "/api/auth/reset-password", json={"token": token, "new_password": "senhaNova123"}
    )
    assert resp.status_code == 400


def test_forgot_password_still_returns_204_if_resend_rejects_the_send(client, monkeypatch):
    """Sandbox do Resend sem domínio verificado só manda pro e-mail que
    criou a API key — qualquer outro destinatário é rejeitado pela API. Isso
    não pode virar 500 nem revelar que o envio falhou (senão dá pra usar
    esse endpoint pra descobrir se um e-mail tem conta ou não)."""

    def failing_send_email(*, to: str, subject: str, html: str) -> None:
        raise EmailSendError()

    monkeypatch.setattr("app.services.auth_service.send_email", failing_send_email)
    client.post(
        "/api/auth/register", json={"email": "resendrecusa@example.com", "password": "senhaAntiga1"}
    )

    resp = client.post(
        "/api/auth/forgot-password",
        json={"email": "resendrecusa@example.com", "reset_url_base": "https://app.exemplo.com"},
    )
    assert resp.status_code == 204
