from datetime import date, timedelta


def test_register_login_and_me(client, auth):
    r = client.get("/auth/me", headers=auth)
    assert r.status_code == 200
    assert r.json()["email"] == "aryan@example.com"


def test_duplicate_email_rejected(client, auth):
    r = client.post("/auth/register", json={"email": "aryan@example.com", "name": "X", "password": "secret123"})
    assert r.status_code == 400


def test_wrong_password_rejected(client, auth):
    r = client.post("/auth/login", data={"username": "aryan@example.com", "password": "nope"})
    assert r.status_code == 401


def test_short_password_rejected(client):
    r = client.post("/auth/register", json={"email": "a@b.com", "name": "A", "password": "123"})
    assert r.status_code == 422


def test_endpoints_require_login(client):
    assert client.get("/expenses/").status_code == 401
    assert client.get("/budgets/").status_code == 401
    assert client.get("/expenses/", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_expense_crud(client, auth, add_expense):
    e = add_expense(title="Lunch", amount=12.5)
    r = client.put(f"/expenses/{e['id']}", json={"amount": 15}, headers=auth)
    assert r.json()["amount"] == 15
    assert r.json()["title"] == "Lunch"
    assert client.delete(f"/expenses/{e['id']}", headers=auth).status_code == 204
    assert client.get(f"/expenses/{e['id']}", headers=auth).status_code == 404


def test_expense_validation(client, auth):
    base = {"title": "X", "amount": 5, "category": "Food & Dining", "date": "2026-01-01"}
    assert client.post("/expenses/", json={**base, "amount": -5}, headers=auth).status_code == 422
    assert client.post("/expenses/", json={**base, "amount": 0}, headers=auth).status_code == 422
    assert client.post("/expenses/", json={**base, "category": "Pizza"}, headers=auth).status_code == 422
    assert client.post("/expenses/", json={**base, "title": ""}, headers=auth).status_code == 422


def test_users_cannot_see_each_others_data(client, auth, make_user, add_expense):
    e = add_expense(title="Private")
    other = make_user(email="other@example.com")
    assert client.get("/expenses/", headers=other).json() == []
    assert client.get(f"/expenses/{e['id']}", headers=other).status_code == 404
    assert client.put(f"/expenses/{e['id']}", json={"amount": 1}, headers=other).status_code == 404
    assert client.delete(f"/expenses/{e['id']}", headers=other).status_code == 404


def test_filters_and_dashboard(client, auth, add_expense):
    today = date.today()
    add_expense(title="Old", amount=10, category="Travel", date=today - timedelta(days=400))
    add_expense(title="New", amount=20, category="Food & Dining", date=today)
    add_expense(title="New2", amount=5, category="Food & Dining", date=today)

    r = client.get("/expenses/", params={"category": "Food & Dining"}, headers=auth)
    assert {e["title"] for e in r.json()} == {"New", "New2"}

    r = client.get("/expenses/", params={"start_date": (today - timedelta(days=30)).isoformat()}, headers=auth)
    assert {e["title"] for e in r.json()} == {"New", "New2"}

    d = client.get("/expenses/dashboard", headers=auth).json()
    assert d["total_spent"] == 35
    assert d["total_this_month"] == 25
    assert d["category_breakdown"][0] == {"category": "Food & Dining", "total": 25, "count": 2}

    d = client.get("/expenses/dashboard", params={"category": "Travel"}, headers=auth).json()
    assert d["total_spent"] == 10


def test_csv_export_neutralises_formulas(client, auth, add_expense):
    add_expense(title="=HYPERLINK(\"http://evil\")", notes="+cmd")
    text = client.get("/expenses/export/csv", headers=auth).text
    assert "'=HYPERLINK" in text
    assert "'+cmd" in text
    assert text.splitlines()[0] == "ID,Title,Amount,Category,Date,Notes"
