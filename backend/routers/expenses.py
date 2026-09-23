import csv
import io
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/expenses", tags=["expenses"])


def csv_safe(value) -> str:
    # stop excel from treating titles like =SUM(...) as formulas
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else text


def expense_query(db: Session, user: models.User, category: Optional[str] = None,
                  start_date: Optional[date] = None, end_date: Optional[date] = None):
    q = db.query(models.Expense).filter(models.Expense.owner_id == user.id)
    if category:
        q = q.filter(models.Expense.category == category)
    if start_date:
        q = q.filter(models.Expense.date >= start_date)
    if end_date:
        q = q.filter(models.Expense.date <= end_date)
    return q

@router.get("/", response_model=list[schemas.ExpenseOut])
def list_expenses(
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return expense_query(db, current_user, category, start_date, end_date)\
        .order_by(models.Expense.date.desc()).all()

@router.post("/", response_model=schemas.ExpenseOut, status_code=201)
def create_expense(expense_in: schemas.ExpenseCreate, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    expense = models.Expense(**expense_in.model_dump(), owner_id=current_user.id)
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense

@router.get("/dashboard", response_model=schemas.DashboardStats)
def dashboard(
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    today = date.today()
    all_expenses = expense_query(db, current_user, category, start_date, end_date).all()
    total_spent = sum(e.amount for e in all_expenses)
    total_this_month = sum(
        e.amount for e in all_expenses
        if e.date.year == today.year and e.date.month == today.month
    )
    category_map: dict[str, dict] = {}
    for e in all_expenses:
        if e.category not in category_map:
            category_map[e.category] = {"total": 0.0, "count": 0}
        category_map[e.category]["total"] += e.amount
        category_map[e.category]["count"] += 1
    category_breakdown = [
        schemas.CategorySummary(category=k, total=round(v["total"], 2), count=v["count"])
        for k, v in sorted(category_map.items(), key=lambda x: -x[1]["total"])
    ]
    return schemas.DashboardStats(
        total_spent=round(total_spent, 2),
        total_this_month=round(total_this_month, 2),
        total_expenses=len(all_expenses),
        category_breakdown=category_breakdown,
    )

@router.get("/export/csv")
def export_csv(
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    expenses = expense_query(db, current_user, category, start_date, end_date)\
        .order_by(models.Expense.date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Amount", "Category", "Date", "Notes"])
    for e in expenses:
        writer.writerow([e.id, csv_safe(e.title), e.amount, e.category, e.date, csv_safe(e.notes)])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=expenses.csv"},
    )

@router.get("/{expense_id}", response_model=schemas.ExpenseOut)
def get_expense(expense_id: int, db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id, models.Expense.owner_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense

@router.put("/{expense_id}", response_model=schemas.ExpenseOut)
def update_expense(expense_id: int, updates: schemas.ExpenseUpdate,
                   db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id, models.Expense.owner_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    for field, value in updates.model_dump(exclude_none=True).items():
        setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense

@router.delete("/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db),
                   current_user: models.User = Depends(get_current_user)):
    expense = db.query(models.Expense).filter(
        models.Expense.id == expense_id, models.Expense.owner_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
