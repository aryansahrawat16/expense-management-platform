from collections import defaultdict
from datetime import date
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
import models


def shift_month(d: date, months: int) -> date:
    index = d.year * 12 + (d.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def spending_by_month(db: Session, owner_id: int, since: date) -> dict[tuple[int, int], dict[str, float]]:
    year = extract("year", models.Expense.date)
    month = extract("month", models.Expense.date)
    rows = (
        db.query(year, month, models.Expense.category, func.sum(models.Expense.amount))
        .filter(models.Expense.owner_id == owner_id, models.Expense.date >= since)
        .group_by(year, month, models.Expense.category)
        .all()
    )
    result: dict[tuple[int, int], dict[str, float]] = defaultdict(dict)
    for y, m, category, total in rows:
        result[(int(y), int(m))][category] = float(total)
    return result


def pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)
