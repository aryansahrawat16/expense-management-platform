import calendar
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from recurring import get_synced_user
from stats import pct_change, shift_month, spending_by_month
import models, schemas

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/trends", response_model=schemas.Trends)
def trends(months: int = Query(6, ge=2, le=24), db: Session = Depends(get_db),
           user: models.User = Depends(get_synced_user)):
    today = date.today()
    by_month = spending_by_month(db, user.id, shift_month(today, -(months - 1)))

    month_totals = []
    for offset in range(months - 1, -1, -1):
        m = shift_month(today, -offset)
        month_totals.append(schemas.MonthTotal(
            month=f"{m.year}-{m.month:02d}",
            total=round(sum(by_month.get((m.year, m.month), {}).values()), 2),
        ))

    last = shift_month(today, -1)
    this_cats = by_month.get((today.year, today.month), {})
    last_cats = by_month.get((last.year, last.month), {})
    this_total, last_total = sum(this_cats.values()), sum(last_cats.values())

    days_in_month = calendar.monthrange(today.year, today.month)[1]
    projected = this_total / today.day * days_in_month

    categories = [
        schemas.CategoryChange(
            category=c,
            this_month=round(this_cats.get(c, 0.0), 2),
            last_month=round(last_cats.get(c, 0.0), 2),
            change_pct=pct_change(this_cats.get(c, 0.0), last_cats.get(c, 0.0)),
        )
        for c in set(this_cats) | set(last_cats)
    ]
    categories.sort(key=lambda c: -abs(c.this_month - c.last_month))

    return schemas.Trends(
        months=month_totals,
        this_month_total=round(this_total, 2),
        last_month_total=round(last_total, 2),
        change_pct=pct_change(this_total, last_total),
        projected_month_total=round(projected, 2),
        categories=categories,
    )
