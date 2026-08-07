"""Testes do dashboard: saldos, resumo, breakdown por categoria e evolução mensal."""
import calendar
from datetime import datetime, timezone


def _create_account(client, headers, name="Conta", initial_balance="0"):
    return client.post(
        "/api/accounts",
        json={"name": name, "type": "checking", "initial_balance": initial_balance},
        headers=headers,
    ).json()


def _create_category(client, headers, name="Categoria", type_="expense"):
    return client.post(
        "/api/categories", json={"name": name, "type": type_}, headers=headers
    ).json()


def _create_transaction(client, headers, account_id, amount, type_, date, category_id=None):
    payload = {"account_id": account_id, "type": type_, "amount": amount, "date": date}
    if category_id:
        payload["category_id"] = category_id
    return client.post("/api/transactions", json=payload, headers=headers).json()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_dashboard_requires_authentication(client):
    resp = client.get("/api/dashboard/balances")
    assert resp.status_code == 401


def test_balances_include_initial_balance_and_transactions(client, auth_headers):
    account = _create_account(client, auth_headers, initial_balance="100.00")
    _create_transaction(client, auth_headers, account["id"], "50.00", "income", _now_iso())
    _create_transaction(client, auth_headers, account["id"], "30.00", "expense", _now_iso())

    resp = client.get("/api/dashboard/balances", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_balance"] == "120.00"
    assert body["accounts"][0]["balance"] == "120.00"


def test_summary_defaults_to_current_month(client, auth_headers):
    account = _create_account(client, auth_headers)
    _create_transaction(client, auth_headers, account["id"], "1000.00", "income", _now_iso())
    _create_transaction(client, auth_headers, account["id"], "400.00", "expense", _now_iso())

    resp = client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_income"] == "1000.00"
    assert body["total_expense"] == "400.00"
    assert body["net"] == "600.00"


def test_summary_includes_transactions_later_in_the_month(client, auth_headers):
    """Regressão: o período padrão ('mês corrente') não pode ir só até 'agora'
    — um lançamento datado mais tarde no mesmo mês precisa contar também."""
    account = _create_account(client, auth_headers)
    now = datetime.now(timezone.utc)
    last_day = calendar.monthrange(now.year, now.month)[1]
    later_this_month = now.replace(day=last_day, hour=23, minute=0, second=0, microsecond=0)

    _create_transaction(
        client, auth_headers, account["id"], "150.00", "expense", later_this_month.isoformat()
    )

    resp = client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total_expense"] == "150.00"


def test_category_breakdown_groups_by_category(client, auth_headers):
    account = _create_account(client, auth_headers)
    food = _create_category(client, auth_headers, "Comida", "expense")
    transport = _create_category(client, auth_headers, "Transporte", "expense")

    _create_transaction(client, auth_headers, account["id"], "100.00", "expense", _now_iso(), food["id"])
    _create_transaction(client, auth_headers, account["id"], "50.00", "expense", _now_iso(), food["id"])
    _create_transaction(
        client, auth_headers, account["id"], "30.00", "expense", _now_iso(), transport["id"]
    )

    resp = client.get("/api/dashboard/by-category", params={"type": "expense"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert body[0]["category_name"] == "Comida"
    assert body[0]["total"] == "150.00"
    assert body[1]["category_name"] == "Transporte"
    assert body[1]["total"] == "30.00"


def test_category_breakdown_includes_uncategorized(client, auth_headers):
    account = _create_account(client, auth_headers)
    _create_transaction(client, auth_headers, account["id"], "20.00", "expense", _now_iso())

    resp = client.get("/api/dashboard/by-category", params={"type": "expense"}, headers=auth_headers)
    body = resp.json()
    assert len(body) == 1
    assert body[0]["category_id"] is None
    assert body[0]["category_name"] == "Sem categoria"


def test_monthly_evolution_returns_fixed_window(client, auth_headers):
    account = _create_account(client, auth_headers)
    _create_transaction(client, auth_headers, account["id"], "500.00", "income", _now_iso())

    resp = client.get(
        "/api/dashboard/monthly-evolution", params={"months": 3}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3

    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    assert body[-1]["month"] == current_month
    assert body[-1]["income"] == "500.00"
    assert body[-1]["expense"] == "0"
    # meses sem transação vêm zerados, não somem da lista
    assert body[0]["income"] == "0"
