from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from stats import shift_month, spending_by_month
import models, schemas

router = APIRouter(prefix="/budgets", tags=["budgets"])

WARNING_THRESHOLD = 80.0


def budget_statuses(db: Session, user: models.User) -> list[schemas.BudgetStatus]:
    today = date.today()
    spent = spending_by_month(db, user.id, shift_month(today, 0)).get((today.year, today.month), {})
    budgets = db.query(models.Budget).filter(models.Budget.owner_id == user.id).all()
    statuses = []
    for b in budgets:
        s = round(spent.get(b.category, 0.0), 2)
        exact_percent = s / b.monthly_limit * 100
        status = "over" if s > b.monthly_limit else "warning" if exact_percent >= WARNING_THRESHOLD else "ok"
        percent = round(exact_percent, 1)
        statuses.append(schemas.BudgetStatus(
            id=b.id, category=b.category, monthly_limit=b.monthly_limit, spent=s,
            remaining=round(b.monthly_limit - s, 2), percent=percent, status=status,
        ))
    return sorted(statuses, key=lambda x: -x.percent)


@router.get("/", response_model=list[schemas.BudgetStatus])
def list_budgets(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return budget_statuses(db, user)


@router.put("/", response_model=list[schemas.BudgetStatus])
def upsert_budget(body: schemas.BudgetIn, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    budget = db.query(models.Budget).filter(
        models.Budget.owner_id == user.id, models.Budget.category == body.category
    ).first()
    if budget:
        budget.monthly_limit = body.monthly_limit
    else:
        db.add(models.Budget(owner_id=user.id, category=body.category, monthly_limit=body.monthly_limit))
    db.commit()
    return budget_statuses(db, user)


@router.delete("/{budget_id}", status_code=204)
def delete_budget(budget_id: int, db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    budget = db.query(models.Budget).filter(
        models.Budget.id == budget_id, models.Budget.owner_id == user.id
    ).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(budget)
    db.commit()
