import calendar
from datetime import date

from stats import shift_month


def set_budget(client, auth, category, limit):
    r = client.put("/budgets/", json={"category": category, "monthly_limit": limit}, headers=auth)
    assert r.status_code == 200, r.text
    return {b["category"]: b for b in r.json()}


def test_budget_status_thresholds(client, auth, add_expense):
    add_expense(amount=79.99, category="Food & Dining")
    add_expense(amount=80, category="Travel")
    add_expense(amount=100, category="Shopping")
    add_expense(amount=100.01, category="Education")
    set_budget(client, auth, "Food & Dining", 100)
    set_budget(client, auth, "Travel", 100)
    set_budget(client, auth, "Shopping", 100)
    budgets = set_budget(client, auth, "Education", 100)

    assert budgets["Food & Dining"]["status"] == "ok"
    assert budgets["Travel"]["status"] == "warning"      # exactly 80%
    assert budgets["Shopping"]["status"] == "warning"    # exactly at the limit is not over
    assert budgets["Education"]["status"] == "over"
    assert budgets["Education"]["remaining"] == -0.01


def test_budget_only_counts_this_month(client, auth, add_expense):
    add_expense(amount=500, category="Travel", date=shift_month(date.today(), -1))
    add_expense(amount=20, category="Travel")
    budgets = set_budget(client, auth, "Travel", 100)
    assert budgets["Travel"]["spent"] == 20


def test_budget_upsert_updates_instead_of_duplicating(client, auth):
    set_budget(client, auth, "Travel", 100)
    budgets = set_budget(client, auth, "Travel", 250)
    assert len(budgets) == 1
    assert budgets["Travel"]["monthly_limit"] == 250


def test_budget_delete_and_isolation(client, auth, make_user):
    b = set_budget(client, auth, "Travel", 100)["Travel"]
    other = make_user(email="other@example.com")
    assert client.delete(f"/budgets/{b['id']}", headers=other).status_code == 404
    assert client.delete(f"/budgets/{b['id']}", headers=auth).status_code == 204
    assert client.get("/budgets/", headers=auth).json() == []


def test_trends(client, auth, add_expense):
    today = date.today()
    add_expense(amount=50, category="Food & Dining", date=today)
    add_expense(amount=40, category="Food & Dining", date=shift_month(today, -1))
    add_expense(amount=10, category="Travel", date=shift_month(today, -3))
    add_expense(amount=999, category="Travel", date=shift_month(today, -12))  # outside the window

    t = client.get("/insights/trends", params={"months": 6}, headers=auth).json()

    assert len(t["months"]) == 6
    assert t["months"][-1] == {"month": f"{today.year}-{today.month:02d}", "total": 50}
    assert t["months"][-2]["total"] == 40
    assert t["months"][-4]["total"] == 10
    assert sum(m["total"] for m in t["months"]) == 100
    assert t["change_pct"] == 25.0
    days = calendar.monthrange(today.year, today.month)[1]
    assert t["projected_month_total"] == round(50 / today.day * days, 2)
    assert t["categories"] == [
        {"category": "Food & Dining", "this_month": 50, "last_month": 40, "change_pct": 25.0}
    ]


def test_trends_with_no_previous_month(client, auth, add_expense):
    add_expense(amount=30, category="Travel")
    t = client.get("/insights/trends", headers=auth).json()
    assert t["change_pct"] is None
    assert t["categories"][0]["change_pct"] is None
