import atexit
import os
import tempfile

# Point the app at a throwaway SQLite file instead of the real Postgres DB,
# and set these BEFORE importing anything from `app` so database.py / security.py
# pick them up (python-dotenv's load_dotenv() never overrides vars already set).
_tmp_db_fd, _tmp_db_path = tempfile.mkstemp(suffix=".db")
os.close(_tmp_db_fd)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp_db_path}")
os.environ.setdefault("JWT_SECRET", "test-secret-key-not-for-production")
atexit.register(lambda: os.path.exists(_tmp_db_path) and os.remove(_tmp_db_path))

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def _clean_tables():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    client.post("/signup", json={"email": "test@example.com", "password": "testpass123"})
    resp = client.post("/login", data={"username": "test@example.com", "password": "testpass123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
