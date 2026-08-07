"""Testes de metas financeiras."""


def _create_goal(client, headers, name="Viagem", target_amount="5000.00", target_date=None):
    payload = {"name": name, "target_amount": target_amount}
    if target_date:
        payload["target_date"] = target_date
    return client.post("/api/goals", json=payload, headers=headers).json()


def test_create_and_list_goal(client, auth_headers):
    resp = client.post(
        "/api/goals",
        json={"name": "Viagem", "target_amount": "5000.00", "target_date": "2026-12-31"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Viagem"
    assert body["current_amount"] == "0.00" or body["current_amount"] == "0"
    assert body["progress_percent"] == "0.00"

    resp = client.get("/api/goals", headers=auth_headers)
    assert len(resp.json()) == 1


def test_goals_require_authentication(client):
    resp = client.get("/api/goals")
    assert resp.status_code == 401


def test_target_amount_must_be_positive(client, auth_headers):
    resp = client.post(
        "/api/goals", json={"name": "Meta inválida", "target_amount": "0"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_contribute_increases_current_amount_and_progress(client, auth_headers):
    goal = _create_goal(client, auth_headers, target_amount="1000.00")

    resp = client.post(
        f"/api/goals/{goal['id']}/contribute", json={"amount": "250.00"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["current_amount"] == "250.00"
    assert body["progress_percent"] == "25.00"


def test_contribute_can_go_over_100_percent(client, auth_headers):
    goal = _create_goal(client, auth_headers, target_amount="100.00")
    resp = client.post(
        f"/api/goals/{goal['id']}/contribute", json={"amount": "150.00"}, headers=auth_headers
    )
    assert resp.json()["progress_percent"] == "150.00"


def test_negative_contribution_withdraws(client, auth_headers):
    goal = _create_goal(client, auth_headers, target_amount="1000.00")
    client.post(f"/api/goals/{goal['id']}/contribute", json={"amount": "300.00"}, headers=auth_headers)
    resp = client.post(
        f"/api/goals/{goal['id']}/contribute", json={"amount": "-100.00"}, headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["current_amount"] == "200.00"


def test_contribution_cannot_make_current_amount_negative(client, auth_headers):
    goal = _create_goal(client, auth_headers, target_amount="1000.00")
    resp = client.post(
        f"/api/goals/{goal['id']}/contribute", json={"amount": "-50.00"}, headers=auth_headers
    )
    assert resp.status_code == 400


def test_zero_contribution_rejected_by_validation(client, auth_headers):
    goal = _create_goal(client, auth_headers)
    resp = client.post(
        f"/api/goals/{goal['id']}/contribute", json={"amount": "0"}, headers=auth_headers
    )
    assert resp.status_code == 422


def test_update_goal_does_not_touch_current_amount(client, auth_headers):
    goal = _create_goal(client, auth_headers, target_amount="1000.00")
    client.post(f"/api/goals/{goal['id']}/contribute", json={"amount": "400.00"}, headers=auth_headers)

    resp = client.put(
        f"/api/goals/{goal['id']}", json={"name": "Viagem pra praia"}, headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Viagem pra praia"
    assert body["current_amount"] == "400.00"


def test_delete_goal(client, auth_headers):
    goal = _create_goal(client, auth_headers)
    resp = client.delete(f"/api/goals/{goal['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(f"/api/goals/{goal['id']}", headers=auth_headers).status_code == 404


def test_cannot_access_another_users_goal(client, auth_headers):
    goal = _create_goal(client, auth_headers)

    client.post("/api/auth/register", json={"email": "outro3@example.com", "password": "senha1234"})
    login = client.post("/api/auth/login", json={"email": "outro3@example.com", "password": "senha1234"})
    other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    resp = client.get(f"/api/goals/{goal['id']}", headers=other_headers)
    assert resp.status_code == 404

    resp = client.post(
        f"/api/goals/{goal['id']}/contribute", json={"amount": "10.00"}, headers=other_headers
    )
    assert resp.status_code == 404
