"""Testes de contas financeiras."""


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
