import os

# has to happen before importing the app. CI sets DATABASE_URL to postgres
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.pop("AI_API_KEY", None)

from datetime import date

import pytest
from fastapi.testclient import TestClient

from database import Base, engine
from main import app


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_user(client):
    def _make(email="aryan@example.com", password="secret123", name="Aryan"):
        r = client.post("/auth/register", json={"email": email, "name": name, "password": password})
        assert r.status_code == 201, r.text
        r = client.post("/auth/login", data={"username": email, "password": password})
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _make


@pytest.fixture
def auth(make_user):
    return make_user()


@pytest.fixture
def add_expense(client, auth):
    def _add(headers=None, **fields):
        body = {"title": "Coffee", "amount": 5.0, "category": "Food & Dining", "date": date.today().isoformat()}
        body.update({k: (v.isoformat() if isinstance(v, date) else v) for k, v in fields.items()})
        r = client.post("/expenses/", json=body, headers=headers or auth)
        assert r.status_code == 201, r.text
        return r.json()
    return _add
