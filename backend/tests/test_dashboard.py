"""Testes do dashboard: saldos, resumo, breakdown por categoria e evolução mensal."""
from datetime import datetime, timedelta, timezone

from app.services.dashboard_service import _cycle_period, _closing_instant


def _parse(iso: str) -> datetime:
    # Pydantic serializa datetime UTC com sufixo "Z"; datetime.fromisoformat
    # só entende "+00:00" antes do Python 3.11 — normaliza pra comparar.
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


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


def test_summary_includes_transactions_at_end_of_cycle(client, auth_headers):
    """Regressão: o período padrão (ciclo financeiro do usuário) não pode ir
    só até 'agora' — um lançamento datado mais tarde no mesmo ciclo precisa
    contar também, mesmo perto do fechamento."""
    account = _create_account(client, auth_headers)
    now = datetime.now(timezone.utc)
    _, cycle_end = _cycle_period(24, now)  # 24 é o cycle_closing_day padrão do usuário

    _create_transaction(
        client, auth_headers, account["id"], "150.00", "expense", cycle_end.isoformat()
    )

    resp = client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total_expense"] == "150.00"


def test_summary_uses_cycle_closing_day_not_calendar_month(client, auth_headers):
    """O período padrão do resumo é o ciclo financeiro do usuário (fecha no
    dia configurado, igual fatura de cartão) — não o mês calendário. Um
    lançamento logo depois do fechamento já pertence ao PRÓXIMO ciclo e não
    deve entrar no resumo do ciclo atual."""
    client.patch("/api/auth/me", json={"cycle_closing_day": 15}, headers=auth_headers)
    account = _create_account(client, auth_headers)

    now = datetime.now(timezone.utc)
    _, cycle_end = _cycle_period(15, now)
    next_cycle_start = cycle_end + timedelta(microseconds=1)

    _create_transaction(
        client, auth_headers, account["id"], "80.00", "expense", cycle_end.isoformat()
    )
    _create_transaction(
        client, auth_headers, account["id"], "999.00", "expense", next_cycle_start.isoformat()
    )

    resp = client.get("/api/dashboard/summary", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total_expense"] == "80.00"


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


def test_weekly_summary_defaults_to_current_week(client, auth_headers):
    account = _create_account(client, auth_headers, initial_balance="100.00")
    _create_transaction(client, auth_headers, account["id"], "200.00", "income", _now_iso())
    _create_transaction(client, auth_headers, account["id"], "80.00", "expense", _now_iso())

    resp = client.get("/api/dashboard/weekly", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    today = datetime.now(timezone.utc).date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    assert body["week_start"] == monday.isoformat()
    assert body["week_end"] == sunday.isoformat()
    assert body["total_income"] == "200.00"
    assert body["total_expense"] == "80.00"
    assert body["net"] == "120.00"
    # saldo total é o saldo geral das contas (100 inicial + 200 - 80), não só da semana
    assert body["total_balance"] == "220.00"
    assert len(body["days"]) == 7


def test_weekly_summary_groups_by_day_of_week(client, auth_headers):
    account = _create_account(client, auth_headers)
    today = datetime.now(timezone.utc)
    monday = today - timedelta(days=today.weekday())
    wednesday = monday + timedelta(days=2)

    _create_transaction(
        client, auth_headers, account["id"], "60.00", "expense", wednesday.isoformat()
    )

    resp = client.get("/api/dashboard/weekly", headers=auth_headers)
    body = resp.json()

    wednesday_entry = next(d for d in body["days"] if d["date"] == wednesday.date().isoformat())
    assert wednesday_entry["expense"] == "60.00"
    # dias sem lançamento vêm zerados, não somem da lista de 7 dias
    other_days = [d for d in body["days"] if d["date"] != wednesday.date().isoformat()]
    assert all(d["expense"] == "0" and d["income"] == "0" for d in other_days)


def test_weekly_summary_accepts_week_start_for_navigation(client, auth_headers):
    account = _create_account(client, auth_headers)
    today = datetime.now(timezone.utc)
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(days=7)

    _create_transaction(
        client, auth_headers, account["id"], "40.00", "income", last_monday.isoformat()
    )

    resp = client.get(
        "/api/dashboard/weekly",
        params={"week_start": last_monday.date().isoformat()},
        headers=auth_headers,
    )
    body = resp.json()
    assert body["week_start"] == last_monday.date().isoformat()
    assert body["total_income"] == "40.00"

    # semana atual não deve enxergar o lançamento da semana passada
    resp_current = client.get("/api/dashboard/weekly", headers=auth_headers)
    assert resp_current.json()["total_income"] == "0"


def test_cycle_view_shows_only_open_before_closing_day(client, auth_headers):
    """Igual fatura de cartão: enquanto o ciclo corrente ainda não fechou
    (hoje ainda não passou do dia de fechamento desse mês), só existe uma
    fatura relevante — não faz sentido mostrar uma "próxima" vazia."""
    now = datetime.now(timezone.utc)
    client.patch("/api/auth/me", json={"cycle_closing_day": now.day}, headers=auth_headers)

    resp = client.get("/api/dashboard/cycle-view", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["closed"] is None

    expected_start, expected_end = _cycle_period(now.day, now)
    assert _parse(body["open"]["date_from"]) == expected_start
    assert _parse(body["open"]["date_to"]) == expected_end


def test_cycle_view_shows_closed_and_open_after_closing_day(client, auth_headers):
    """Depois que o ciclo fecha (hoje já passou do dia de fechamento desse
    mês), mostra os dois: o que fechou (fatura a pagar) e o novo em aberto
    (já acumulando, mesmo antes de pagar o anterior)."""
    now = datetime.now(timezone.utc)
    closing_day = 1  # sempre no passado dentro do mês, exceto se "hoje" for dia 1
    client.patch("/api/auth/me", json={"cycle_closing_day": closing_day}, headers=auth_headers)

    resp = client.get("/api/dashboard/cycle-view", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["closed"] is not None

    this_month_close = _closing_instant(closing_day, now.year, now.month)
    expected_closed_start, expected_closed_end = _cycle_period(closing_day, this_month_close)
    expected_open_start, expected_open_end = _cycle_period(closing_day, now)

    assert _parse(body["closed"]["date_from"]) == expected_closed_start
    assert _parse(body["closed"]["date_to"]) == expected_closed_end
    assert _parse(body["open"]["date_from"]) == expected_open_start
    assert _parse(body["open"]["date_to"]) == expected_open_end

    # o fechado termina exatamente onde o aberto começa (sem buraco nem sobreposição)
    assert expected_open_start - expected_closed_end == timedelta(microseconds=1)


def test_cycle_view_requires_authentication(client):
    resp = client.get("/api/dashboard/cycle-view")
    assert resp.status_code == 401
