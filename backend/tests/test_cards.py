"""Testes de cartões de crédito e compras parceladas."""


def _create_card(client, headers, name="Nubank", closing_day=20, due_day=27, limit="5000.00"):
    return client.post(
        "/api/cards",
        json={"name": name, "closing_day": closing_day, "due_day": due_day, "limit": limit},
        headers=headers,
    ).json()


def test_create_and_list_card(client, auth_headers):
    resp = client.post(
        "/api/cards",
        json={"name": "Nubank", "closing_day": 20, "due_day": 27, "limit": "5000.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Nubank"
    assert body["closing_day"] == 20

    resp = client.get("/api/cards", headers=auth_headers)
    assert len(resp.json()) == 1


def test_cards_require_authentication(client):
    resp = client.get("/api/cards")
    assert resp.status_code == 401


def test_invalid_closing_day_fails_validation(client, auth_headers):
    resp = client.post(
        "/api/cards",
        json={"name": "Nubank", "closing_day": 35, "due_day": 10, "limit": "1000.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_get_update_delete_card(client, auth_headers):
    card = _create_card(client, auth_headers)

    get_resp = client.get(f"/api/cards/{card['id']}", headers=auth_headers)
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/api/cards/{card['id']}", json={"name": "Nubank Ultravioleta"}, headers=auth_headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Nubank Ultravioleta"

    delete_resp = client.delete(f"/api/cards/{card['id']}", headers=auth_headers)
    assert delete_resp.status_code == 204

    assert client.get(f"/api/cards/{card['id']}", headers=auth_headers).status_code == 404


def test_installment_purchase_before_closing_day_starts_in_purchase_month(client, auth_headers):
    """Aceite da Sprint 6: uma compra em 3x gera 3 lançamentos corretos nos
    meses seguintes. Fechamento dia 20 — compra dia 10 entra na fatura do
    próprio mês de compra."""
    card = _create_card(client, auth_headers, closing_day=20, due_day=27)

    resp = client.post(
        f"/api/cards/{card['id']}/purchases",
        json={
            "description": "Notebook",
            "total_amount": "3000.00",
            "installments": 3,
            "purchase_date": "2026-03-10",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    installments = resp.json()
    assert len(installments) == 3

    months = [t["date"][:7] for t in installments]
    assert months == ["2026-03", "2026-04", "2026-05"]

    amounts = [t["amount"] for t in installments]
    assert amounts == ["1000.00", "1000.00", "1000.00"]

    for i, t in enumerate(installments, start=1):
        assert t["installment_number"] == i
        assert t["installment_total"] == 3
        assert t["description"] == f"Notebook ({i}/3)"
        assert t["date"][8:10] == "27"  # dia de vencimento


def test_installment_purchase_after_closing_day_starts_next_month(client, auth_headers):
    """Compra depois do fechamento entra só na fatura do mês seguinte."""
    card = _create_card(client, auth_headers, closing_day=20, due_day=27)

    resp = client.post(
        f"/api/cards/{card['id']}/purchases",
        json={
            "description": "Celular",
            "total_amount": "600.00",
            "installments": 2,
            "purchase_date": "2026-03-25",
        },
        headers=auth_headers,
    )
    installments = resp.json()
    months = [t["date"][:7] for t in installments]
    assert months == ["2026-04", "2026-05"]


def test_installment_split_adjusts_last_installment_for_rounding(client, auth_headers):
    """R$100 / 3 não pode virar 33.33 x3 = 99.99 — a última parcela absorve o resto."""
    card = _create_card(client, auth_headers)

    resp = client.post(
        f"/api/cards/{card['id']}/purchases",
        json={"total_amount": "100.00", "installments": 3, "purchase_date": "2026-01-05"},
        headers=auth_headers,
    )
    amounts = [t["amount"] for t in resp.json()]
    assert amounts == ["33.33", "33.33", "33.34"]
    assert sum(float(a) for a in amounts) == 100.00


def test_single_installment_purchase_has_no_number_suffix(client, auth_headers):
    card = _create_card(client, auth_headers)
    resp = client.post(
        f"/api/cards/{card['id']}/purchases",
        json={
            "description": "Farmácia",
            "total_amount": "50.00",
            "installments": 1,
            "purchase_date": "2026-01-05",
        },
        headers=auth_headers,
    )
    body = resp.json()
    assert len(body) == 1
    assert body[0]["description"] == "Farmácia"


def test_due_day_clamped_to_last_day_of_short_month(client, auth_headers):
    """Vencimento dia 31 num cartão, mas a parcela cai em fevereiro (28/29 dias)."""
    card = _create_card(client, auth_headers, closing_day=20, due_day=31)

    resp = client.post(
        f"/api/cards/{card['id']}/purchases",
        json={"total_amount": "200.00", "installments": 2, "purchase_date": "2026-01-10"},
        headers=auth_headers,
    )
    installments = resp.json()
    # primeira parcela: janeiro (31 dias, vencimento dia 31 normal)
    assert installments[0]["date"][:10] == "2026-01-31"
    # segunda parcela: fevereiro/2026 não é bissexto, tem 28 dias -> clampa pro dia 28
    assert installments[1]["date"][:10] == "2026-02-28"


def test_purchase_with_invalid_category_fails(client, auth_headers):
    card = _create_card(client, auth_headers)
    resp = client.post(
        f"/api/cards/{card['id']}/purchases",
        json={
            "category_id": "id-invalido",
            "total_amount": "50.00",
            "installments": 1,
            "purchase_date": "2026-01-05",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_purchase_on_invalid_card_fails(client, auth_headers):
    resp = client.post(
        "/api/cards/id-invalido/purchases",
        json={"total_amount": "50.00", "installments": 1, "purchase_date": "2026-01-05"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_get_invoice_returns_installments_for_month(client, auth_headers):
    card = _create_card(client, auth_headers, closing_day=20, due_day=27)
    client.post(
        f"/api/cards/{card['id']}/purchases",
        json={
            "description": "Notebook",
            "total_amount": "3000.00",
            "installments": 3,
            "purchase_date": "2026-03-10",
        },
        headers=auth_headers,
    )
    client.post(
        f"/api/cards/{card['id']}/purchases",
        json={
            "description": "Mercado",
            "total_amount": "200.00",
            "installments": 1,
            "purchase_date": "2026-04-05",
        },
        headers=auth_headers,
    )

    resp = client.get(f"/api/cards/{card['id']}/invoice", params={"month": "2026-04"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == "1200.00"
    assert len(body["installments"]) == 2


def test_delete_purchase_removes_all_installments(client, auth_headers):
    card = _create_card(client, auth_headers)
    resp = client.post(
        f"/api/cards/{card['id']}/purchases",
        json={"total_amount": "300.00", "installments": 3, "purchase_date": "2026-01-05"},
        headers=auth_headers,
    )
    purchase_group_id = resp.json()[0]["purchase_group_id"]

    delete_resp = client.delete(f"/api/cards/purchases/{purchase_group_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    invoice = client.get(
        f"/api/cards/{card['id']}/invoice", params={"month": "2026-01"}, headers=auth_headers
    ).json()
    assert invoice["total"] == "0"


def test_deleting_card_cascades_installments(client, auth_headers):
    card = _create_card(client, auth_headers)
    client.post(
        f"/api/cards/{card['id']}/purchases",
        json={"total_amount": "300.00", "installments": 3, "purchase_date": "2026-01-05"},
        headers=auth_headers,
    )

    client.delete(f"/api/cards/{card['id']}", headers=auth_headers)

    # a transação sumiu junto (não dá mais pra consultar a fatura de um cartão que não existe)
    resp = client.get(f"/api/cards/{card['id']}/invoice", params={"month": "2026-01"}, headers=auth_headers)
    assert resp.status_code == 404


def test_cannot_access_another_users_card(client, auth_headers):
    card = _create_card(client, auth_headers)

    client.post("/api/auth/register", json={"email": "outro2@example.com", "password": "senha1234"})
    login = client.post("/api/auth/login", json={"email": "outro2@example.com", "password": "senha1234"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = client.get(f"/api/cards/{card['id']}", headers=other_headers)
    assert resp.status_code == 404
