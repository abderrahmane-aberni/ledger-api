def test_signup_creates_user(client):
    resp = client.post("/signup", json={"email": "alice@example.com", "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "password" not in data


def test_signup_duplicate_email_rejected(client):
    client.post("/signup", json={"email": "bob@example.com", "password": "secret123"})
    resp = client.post("/signup", json={"email": "bob@example.com", "password": "other123"})
    assert resp.status_code == 400


def test_login_success(client):
    client.post("/signup", json={"email": "carol@example.com", "password": "secret123"})
    resp = client.post("/login", data={"username": "carol@example.com", "password": "secret123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_rejected(client):
    client.post("/signup", json={"email": "dave@example.com", "password": "secret123"})
    resp = client.post("/login", data={"username": "dave@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    resp = client.get("/categories/")
    assert resp.status_code == 401
