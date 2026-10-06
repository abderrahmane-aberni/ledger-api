def test_create_and_list_category(client, auth_headers):
    resp = client.post("/categories/", json={"name": "Groceries"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Groceries"

    resp = client.get("/categories/", headers=auth_headers)
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Groceries" in names


def test_duplicate_category_rejected(client, auth_headers):
    client.post("/categories/", json={"name": "Rent"}, headers=auth_headers)
    resp = client.post("/categories/", json={"name": "Rent"}, headers=auth_headers)
    assert resp.status_code == 400


def test_delete_category(client, auth_headers):
    resp = client.post("/categories/", json={"name": "Travel"}, headers=auth_headers)
    category_id = resp.json()["id"]
    resp = client.delete(f"/categories/{category_id}", headers=auth_headers)
    assert resp.status_code == 204
    resp = client.get("/categories/", headers=auth_headers)
    assert all(c["id"] != category_id for c in resp.json())
