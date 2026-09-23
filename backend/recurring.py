import calendar
from datetime import date, timedelta
from fastapi import Depends
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
import models


def advance(current: date, frequency: str, anchor_day: int) -> date:
    if frequency == "weekly":
        return current + timedelta(days=7)
    if frequency == "monthly":
        year, month = (current.year + 1, 1) if current.month == 12 else (current.year, current.month + 1)
    else:  # yearly
        year, month = current.year + 1, current.month
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(anchor_day, last_day))


def materialize_due(db: Session, user: models.User, today: date | None = None) -> int:
    today = today or date.today()
    # lock the rows so two requests at once can't both create the same charge
    due = (
        db.query(models.RecurringExpense)
        .filter(
            models.RecurringExpense.owner_id == user.id,
            models.RecurringExpense.active.is_(True),
            models.RecurringExpense.next_date <= today,
        )
        .with_for_update()
        .all()
    )
    created = 0
    for r in due:
        while r.next_date <= today:
            db.add(models.Expense(
                title=r.title, amount=r.amount, category=r.category,
                date=r.next_date, notes=r.notes or "Recurring", owner_id=user.id,
            ))
            r.next_date = advance(r.next_date, r.frequency, r.anchor_day)
            created += 1
    if due:
        db.commit()
    return created


def get_synced_user(
    user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
) -> models.User:
    materialize_due(db, user)
    return user
