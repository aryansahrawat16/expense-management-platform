from datetime import date, timedelta

from database import SessionLocal
from recurring import advance
import models


def test_monthly_keeps_the_original_day_after_short_months():
    d = date(2026, 1, 31)
    d = advance(d, "monthly", 31)
    assert d == date(2026, 2, 28)
    d = advance(d, "monthly", 31)
    assert d == date(2026, 3, 31)
    assert advance(date(2026, 4, 30), "monthly", 31) == date(2026, 5, 31)


def test_monthly_handles_leap_years_and_december():
    assert advance(date(2028, 1, 31), "monthly", 31) == date(2028, 2, 29)
    assert advance(date(2026, 12, 15), "monthly", 15) == date(2027, 1, 15)


def test_weekly_and_yearly():
    assert advance(date(2026, 12, 29), "weekly", 29) == date(2027, 1, 5)
    assert advance(date(2028, 2, 29), "yearly", 29) == date(2029, 2, 28)


def create_weekly(client, auth, days_ago=14, **extra):
    body = {"title": "Gym", "amount": 10, "category": "Health & Medical", "frequency": "weekly",
            "start_date": (date.today() - timedelta(days=days_ago)).isoformat(), **extra}
    r = client.post("/recurring/", json=body, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def gym_count(client, auth):
    return sum(1 for e in client.get("/expenses/", headers=auth).json() if e["title"] == "Gym")


def test_backfills_past_charges_once(client, auth):
    r = create_weekly(client, auth, days_ago=14)
    assert r["next_date"] == (date.today() + timedelta(days=7)).isoformat()
    assert gym_count(client, auth) == 3  # 14 days ago, 7 days ago, today
    client.get("/recurring/", headers=auth)
    client.get("/expenses/dashboard", headers=auth)
    assert gym_count(client, auth) == 3


def test_future_start_creates_nothing_yet(client, auth):
    create_weekly(client, auth, days_ago=-3)
    assert gym_count(client, auth) == 0


def test_resume_skips_the_paused_period(client, auth):
    r = create_weekly(client, auth, days_ago=14)
    client.patch(f"/recurring/{r['id']}", json={"active": False}, headers=auth)

    # Simulate three weeks passing while paused
    with SessionLocal() as db:
        db.get(models.RecurringExpense, r["id"]).next_date = date.today() - timedelta(days=21)
        db.commit()
    assert gym_count(client, auth) == 3

    resumed = client.patch(f"/recurring/{r['id']}", json={"active": True}, headers=auth).json()
    assert resumed["next_date"] == date.today().isoformat()
    assert gym_count(client, auth) == 4  # only today's charge, not the three missed weeks


def test_validation_and_isolation(client, auth, make_user):
    too_old = (date.today() - timedelta(days=400)).isoformat()
    base = {"title": "X", "amount": 1, "category": "Other", "frequency": "monthly", "start_date": too_old}
    assert client.post("/recurring/", json=base, headers=auth).status_code == 422
    assert client.post("/recurring/", json={**base, "start_date": date.today().isoformat(), "frequency": "daily"},
                       headers=auth).status_code == 422

    r = create_weekly(client, auth)
    other = make_user(email="other@example.com")
    assert client.patch(f"/recurring/{r['id']}", json={"active": False}, headers=other).status_code == 404
    assert client.delete(f"/recurring/{r['id']}", headers=other).status_code == 404
