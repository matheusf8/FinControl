"""Testes de transações (lançamentos), incluindo filtros e regras de integridade."""


def _create_account(client, headers, name="Conta"):
    return client.post("/api/accounts", json={"name": name, "type": "checking"}, headers=headers).json()


def _create_category(client, headers, name="Categoria", type_="expense"):
    return client.post(
        "/api/categories", json={"name": name, "type": type_}, headers=headers
    ).json()


def test_create_transaction(client, auth_headers):
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers)

    resp = client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "category_id": category["id"],
            "type": "expense",
            "amount": "150.00",
            "description": "Supermercado",
            "date": "2026-08-05T10:00:00",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["amount"] == "150.00"
    assert body["description"] == "Supermercado"


def test_create_transaction_with_invalid_account_fails(client, auth_headers):
    resp = client.post(
        "/api/transactions",
        json={
            "account_id": "id-invalido",
            "type": "expense",
            "amount": "10.00",
            "date": "2026-08-05T10:00:00",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_amount_must_be_positive(client, auth_headers):
    account = _create_account(client, auth_headers)
    resp = client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "type": "expense",
            "amount": "-10.00",
            "date": "2026-08-05T10:00:00",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_filters(client, auth_headers):
    account = _create_account(client, auth_headers)
    food = _create_category(client, auth_headers, "Comida", "expense")
    salary = _create_category(client, auth_headers, "Salário", "income")

    client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "category_id": food["id"],
            "type": "expense",
            "amount": "50.00",
            "date": "2026-08-01T10:00:00",
        },
        headers=auth_headers,
    )
    client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "category_id": salary["id"],
            "type": "income",
            "amount": "3000.00",
            "date": "2026-08-05T10:00:00",
        },
        headers=auth_headers,
    )

    resp = client.get("/api/transactions", params={"type": "income"}, headers=auth_headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["type"] == "income"

    resp = client.get("/api/transactions", params={"category_id": food["id"]}, headers=auth_headers)
    assert len(resp.json()) == 1
    assert resp.json()[0]["amount"] == "50.00"

    resp = client.get(
        "/api/transactions", params={"date_from": "2026-08-03T00:00:00"}, headers=auth_headers
    )
    assert len(resp.json()) == 1
    assert resp.json()[0]["type"] == "income"


def test_delete_transaction(client, auth_headers):
    account = _create_account(client, auth_headers)
    created = client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "type": "expense",
            "amount": "20.00",
            "date": "2026-08-01T10:00:00",
        },
        headers=auth_headers,
    ).json()

    resp = client.delete(f"/api/transactions/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/api/transactions/{created['id']}", headers=auth_headers)
    assert resp.status_code == 404


def test_deleting_account_cascades_transactions(client, auth_headers):
    account = _create_account(client, auth_headers)
    created = client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "type": "expense",
            "amount": "20.00",
            "date": "2026-08-01T10:00:00",
        },
        headers=auth_headers,
    ).json()

    client.delete(f"/api/accounts/{account['id']}", headers=auth_headers)

    resp = client.get(f"/api/transactions/{created['id']}", headers=auth_headers)
    assert resp.status_code == 404


def test_list_transactions_includes_card_installments(client, auth_headers):
    """Regressão: GET /api/transactions quebrava com 500 quando havia parcela
    de cartão na lista, porque TransactionResponse.account_id exigia string
    (parcela de cartão tem account_id=None, ver Sprint 6)."""
    account = _create_account(client, auth_headers)
    client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "type": "expense",
            "amount": "50.00",
            "date": "2026-08-01T10:00:00",
        },
        headers=auth_headers,
    )

    card = client.post(
        "/api/cards",
        json={"name": "Cartao", "closing_day": 20, "due_day": 27, "limit": "1000.00"},
        headers=auth_headers,
    ).json()
    client.post(
        f"/api/cards/{card['id']}/purchases",
        json={"total_amount": "90.00", "installments": 3, "purchase_date": "2026-01-05"},
        headers=auth_headers,
    )

    resp = client.get("/api/transactions", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 4  # 1 lançamento de conta + 3 parcelas de cartão

    card_txs = [t for t in body if t["card_id"] is not None]
    account_txs = [t for t in body if t["account_id"] is not None]
    assert len(card_txs) == 3
    assert len(account_txs) == 1
    assert all(t["account_id"] is None for t in card_txs)
    assert all(t["card_id"] is None for t in account_txs)


def test_update_transaction_changes_only_given_fields(client, auth_headers):
    account = _create_account(client, auth_headers)
    category = _create_category(client, auth_headers)
    created = client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "category_id": category["id"],
            "type": "expense",
            "amount": "50.00",
            "description": "Original",
            "date": "2026-08-19T00:00:00",
        },
        headers=auth_headers,
    ).json()

    # Só manda "date" — descrição, valor, categoria etc devem continuar iguais
    # (exclude_unset no service, não um PUT que zera o resto).
    resp = client.put(
        f"/api/transactions/{created['id']}",
        json={"date": "2026-08-23T00:00:00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["date"].startswith("2026-08-23")
    assert body["amount"] == "50.00"
    assert body["description"] == "Original"
    assert body["category_id"] == category["id"]


def test_update_transaction_amount_and_description(client, auth_headers):
    account = _create_account(client, auth_headers)
    created = client.post(
        "/api/transactions",
        json={
            "account_id": account["id"],
            "type": "expense",
            "amount": "50.00",
            "date": "2026-08-19T00:00:00",
        },
        headers=auth_headers,
    ).json()

    resp = client.put(
        f"/api/transactions/{created['id']}",
        json={"amount": "75.30", "description": "Corrigido"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["amount"] == "75.30"
    assert body["description"] == "Corrigido"


def test_update_transaction_with_invalid_category_fails(client, auth_headers):
    account = _create_account(client, auth_headers)
    created = client.post(
        "/api/transactions",
        json={"account_id": account["id"], "type": "expense", "amount": "50.00", "date": "2026-08-19T00:00:00"},
        headers=auth_headers,
    ).json()

    resp = client.put(
        f"/api/transactions/{created['id']}",
        json={"category_id": "categoria-que-nao-existe"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_update_nonexistent_transaction_returns_404(client, auth_headers):
    resp = client.put(
        "/api/transactions/id-que-nao-existe",
        json={"amount": "10.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_update_transaction_from_another_user_returns_404(client, auth_headers):
    account = _create_account(client, auth_headers)
    created = client.post(
        "/api/transactions",
        json={"account_id": account["id"], "type": "expense", "amount": "50.00", "date": "2026-08-19T00:00:00"},
        headers=auth_headers,
    ).json()

    client.post("/api/auth/register", json={"email": "outro@example.com", "password": "senha1234"})
    other_login = client.post(
        "/api/auth/login", json={"email": "outro@example.com", "password": "senha1234"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    resp = client.put(
        f"/api/transactions/{created['id']}",
        json={"amount": "999.00"},
        headers=other_headers,
    )
    assert resp.status_code == 404
