"""Testes de contas financeiras."""
from datetime import datetime, timezone


def _second_user_headers(client):
    client.post("/api/auth/register", json={"email": "outro@example.com", "password": "senha1234"})
    login = client.post("/api/auth/login", json={"email": "outro@example.com", "password": "senha1234"})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_create_and_list_account(client, auth_headers):
    resp = client.post(
        "/api/accounts",
        json={"name": "Conta Corrente", "type": "checking", "initial_balance": "100.50"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Conta Corrente"
    assert body["initial_balance"] == "100.50"

    resp = client.get("/api/accounts", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_accounts_require_authentication(client):
    resp = client.get("/api/accounts")
    assert resp.status_code == 401


def test_get_update_delete_account(client, auth_headers):
    create = client.post("/api/accounts", json={"name": "Carteira", "type": "wallet"}, headers=auth_headers)
    account_id = create.json()["id"]

    get_resp = client.get(f"/api/accounts/{account_id}", headers=auth_headers)
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/api/accounts/{account_id}", json={"name": "Carteira Nova"}, headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Carteira Nova"

    delete_resp = client.delete(f"/api/accounts/{account_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    get_after_delete = client.get(f"/api/accounts/{account_id}", headers=auth_headers)
    assert get_after_delete.status_code == 404


def test_account_not_found(client, auth_headers):
    resp = client.get("/api/accounts/id-que-nao-existe", headers=auth_headers)
    assert resp.status_code == 404


def test_cannot_access_another_users_account(client, auth_headers):
    create = client.post(
        "/api/accounts", json={"name": "Conta Privada", "type": "checking"}, headers=auth_headers
    )
    account_id = create.json()["id"]

    other_headers = _second_user_headers(client)
    resp = client.get(f"/api/accounts/{account_id}", headers=other_headers)
    assert resp.status_code == 404


def test_account_created_without_real_balance(client, auth_headers):
    resp = client.post("/api/accounts", json={"name": "Conta", "type": "checking"}, headers=auth_headers)
    assert resp.json()["real_balance"] is None


def test_update_real_balance(client, auth_headers):
    create = client.post("/api/accounts", json={"name": "Conta", "type": "checking"}, headers=auth_headers)
    account_id = create.json()["id"]

    resp = client.put(f"/api/accounts/{account_id}", json={"real_balance": "1500.00"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["real_balance"] == "1500.00"


def test_pay_invoice_debits_real_balance_and_abates_closed_cycle(client, auth_headers):
    """Igual pagar uma fatura de cartão de verdade: some do "saldo em conta"
    e abate exatamente esse valor do total da fatura fechada."""
    now = datetime.now(timezone.utc)
    closing_day = 1  # fatura já fechou nesse mês (exceto se "hoje" for dia 1)
    client.patch("/api/auth/me", json={"cycle_closing_day": closing_day}, headers=auth_headers)

    account = client.post(
        "/api/accounts", json={"name": "Conta", "type": "checking"}, headers=auth_headers
    ).json()
    client.put(f"/api/accounts/{account['id']}", json={"real_balance": "1000.00"}, headers=auth_headers)

    client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "type": "expense",
            "amount": "300.00",
            "date": now.replace(day=1).isoformat(),
        },
        headers=auth_headers,
    )

    resp = client.post(
        f"/api/accounts/{account['id']}/pay-invoice", json={"amount": "120.00"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["real_balance"] == "880.00"  # 1000 - 120

    cycle = client.get("/api/dashboard/cycle-view", headers=auth_headers).json()
    assert cycle["closed"] is not None
    summary = client.get(
        "/api/dashboard/summary",
        params={"date_from": cycle["closed"]["date_from"], "date_to": cycle["closed"]["date_to"]},
        headers=auth_headers,
    ).json()
    assert summary["total_expense"] == "180.00"  # 300 - 120 de abatimento


def test_pay_invoice_fails_without_closed_cycle(client, auth_headers):
    now = datetime.now(timezone.utc)
    client.patch("/api/auth/me", json={"cycle_closing_day": now.day}, headers=auth_headers)
    account = client.post(
        "/api/accounts", json={"name": "Conta", "type": "checking"}, headers=auth_headers
    ).json()

    resp = client.post(
        f"/api/accounts/{account['id']}/pay-invoice", json={"amount": "50.00"}, headers=auth_headers
    )
    assert resp.status_code == 409


def test_pay_invoice_requires_authentication(client):
    resp = client.post("/api/accounts/qualquer-id/pay-invoice", json={"amount": "50.00"})
    assert resp.status_code == 401


def test_pay_invoice_on_another_users_account_fails(client, auth_headers):
    account = client.post(
        "/api/accounts", json={"name": "Conta", "type": "checking"}, headers=auth_headers
    ).json()
    other_headers = _second_user_headers(client)
    resp = client.post(
        f"/api/accounts/{account['id']}/pay-invoice", json={"amount": "50.00"}, headers=other_headers
    )
    assert resp.status_code == 404
