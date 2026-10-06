def _make_category(client, headers, name="Groceries"):
    resp = client.post("/categories/", json={"name": name}, headers=headers)
    return resp.json()["id"]


def test_monthly_summary(client, auth_headers):
    category_id = _make_category(client, auth_headers)
    client.post(
        "/transactions/",
        json={"amount": 1000, "type": "income", "category_id": None},
        headers=auth_headers,
    )
    client.post(
        "/transactions/",
        json={"amount": 300, "type": "expense", "category_id": category_id},
        headers=auth_headers,
    )

    resp = client.get("/reports/monthly-summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_income"] == 1000
    assert data["total_expense"] == 300
    assert data["net"] == 700


def test_category_breakdown(client, auth_headers):
    category_id = _make_category(client, auth_headers, "Groceries")
    client.post(
        "/transactions/",
        json={"amount": 50, "type": "expense", "category_id": category_id},
        headers=auth_headers,
    )
    client.post(
        "/transactions/",
        json={"amount": 25, "type": "expense", "category_id": category_id},
        headers=auth_headers,
    )

    resp = client.get("/reports/category-breakdown", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["category_name"] == "Groceries"
    assert data[0]["total"] == 75


def test_budget_alert_over_budget(client, auth_headers):
    category_id = _make_category(client, auth_headers, "Dining")
    client.post("/budgets/", json={"category_id": category_id, "monthly_limit": 50}, headers=auth_headers)
    client.post(
        "/transactions/",
        json={"amount": 80, "type": "expense", "category_id": category_id},
        headers=auth_headers,
    )

    resp = client.get("/reports/budget-alerts", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["over_budget"] is True
    assert data[0]["spent"] == 80

def test_range_summary_default_is_month(client, auth_headers):
    category_id = _make_category(client, auth_headers, "Transport")
    client.post(
        "/transactions/",
        json={"amount": 15, "type": "expense", "category_id": category_id},
        headers=auth_headers,
    )

    resp = client.get("/reports/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["range"] == "month"
    assert data["total_expense"] == 15
    assert data["net"] == -15
    assert data["category_breakdown"][0]["category_name"] == "Transport"


def test_range_summary_accepts_each_range(client, auth_headers):
    for range_value in ["week", "month", "3months", "3years"]:
        resp = client.get(f"/reports/summary?range={range_value}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["range"] == range_value


def test_range_summary_rejects_invalid_range(client, auth_headers):
    resp = client.get("/reports/summary?range=nonsense", headers=auth_headers)
    assert resp.status_code == 422


def test_range_summary_net_is_income_minus_expense(client, auth_headers):
    category_id = _make_category(client, auth_headers, "Salary")
    client.post(
        "/transactions/",
        json={"amount": 500, "type": "income", "category_id": category_id},
        headers=auth_headers,
    )
    client.post(
        "/transactions/",
        json={"amount": 120, "type": "expense", "category_id": category_id},
        headers=auth_headers,
    )

    resp = client.get("/reports/summary?range=week", headers=auth_headers)
    data = resp.json()
    assert data["total_income"] == 500
    assert data["total_expense"] == 120
    assert data["net"] == 380

