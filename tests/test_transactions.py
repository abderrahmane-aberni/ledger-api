def _make_category(client, headers, name="Groceries"):
    resp = client.post("/categories/", json={"name": name}, headers=headers)
    return resp.json()["id"]


def test_create_list_transaction(client, auth_headers):
    category_id = _make_category(client, auth_headers)
    resp = client.post(
        "/transactions/",
        json={"amount": 42.5, "type": "expense", "description": "Weekly shop", "category_id": category_id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount"] == 42.5
    assert data["type"] == "expense"

    resp = client.get("/transactions/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_transaction(client, auth_headers):
    category_id = _make_category(client, auth_headers)
    resp = client.post(
        "/transactions/",
        json={"amount": 10, "type": "expense", "category_id": category_id},
        headers=auth_headers,
    )
    tx_id = resp.json()["id"]

    resp = client.patch(f"/transactions/{tx_id}", json={"amount": 20}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["amount"] == 20


def test_delete_transaction(client, auth_headers):
    category_id = _make_category(client, auth_headers)
    resp = client.post(
        "/transactions/",
        json={"amount": 10, "type": "expense", "category_id": category_id},
        headers=auth_headers,
    )
    tx_id = resp.json()["id"]

    resp = client.delete(f"/transactions/{tx_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get("/transactions/", headers=auth_headers)
    assert all(t["id"] != tx_id for t in resp.json())


def test_transaction_requires_valid_category(client, auth_headers):
    resp = client.post(
        "/transactions/",
        json={"amount": 10, "type": "expense", "category_id": 9999},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_csv_export_import_roundtrip(client, auth_headers):
    category_id = _make_category(client, auth_headers, "Bills")
    client.post(
        "/transactions/",
        json={"amount": 99.99, "type": "expense", "description": "Electricity", "category_id": category_id},
        headers=auth_headers,
    )

    resp = client.get("/transactions/export", headers=auth_headers)
    assert resp.status_code == 200
    csv_content = resp.text
    assert "Electricity" in csv_content

    files = {"file": ("transactions.csv", csv_content, "text/csv")}
    resp = client.post("/transactions/import", headers=auth_headers, files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["created"] == 1
    assert body["errors"] == []
