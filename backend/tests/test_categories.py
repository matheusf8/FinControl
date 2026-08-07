"""Testes de categorias."""


def test_create_and_list_category(client, auth_headers):
    resp = client.post(
        "/api/categories",
        json={"name": "Alimentação", "type": "expense", "color": "#22c55e"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "expense"

    resp = client.get("/api/categories", headers=auth_headers)
    assert len(resp.json()) == 1


def test_category_type_is_not_editable(client, auth_headers):
    create = client.post(
        "/api/categories", json={"name": "Salário", "type": "income"}, headers=auth_headers
    )
    category_id = create.json()["id"]

    # o schema de update nem tem campo "type" — mandar um não muda nada
    update = client.put(
        f"/api/categories/{category_id}",
        json={"name": "Salário CLT", "type": "expense"},
        headers=auth_headers,
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Salário CLT"
    assert update.json()["type"] == "income"


def test_invalid_color_fails_validation(client, auth_headers):
    resp = client.post(
        "/api/categories",
        json={"name": "Lazer", "type": "expense", "color": "vermelho"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_cannot_delete_category_in_use(client, auth_headers):
    account = client.post(
        "/api/accounts", json={"name": "Conta", "type": "checking"}, headers=auth_headers
    ).json()
    category = client.post(
        "/api/categories", json={"name": "Mercado", "type": "expense"}, headers=auth_headers
    ).json()
    client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "category_id": category["id"],
            "type": "expense",
            "amount": "50.00",
            "date": "2026-08-01T12:00:00",
        },
        headers=auth_headers,
    )

    resp = client.delete(f"/api/categories/{category['id']}", headers=auth_headers)
    assert resp.status_code == 409


def test_can_delete_category_without_transactions(client, auth_headers):
    category = client.post(
        "/api/categories", json={"name": "Sem uso", "type": "expense"}, headers=auth_headers
    ).json()
    resp = client.delete(f"/api/categories/{category['id']}", headers=auth_headers)
    assert resp.status_code == 204
