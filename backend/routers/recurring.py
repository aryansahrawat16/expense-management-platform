from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from auth import get_current_user
from database import get_db
from recurring import advance, materialize_due
import models, schemas

router = APIRouter(prefix="/recurring", tags=["recurring"])


def _get_owned(db: Session, user: models.User, recurring_id: int) -> models.RecurringExpense:
    r = db.query(models.RecurringExpense).filter(
        models.RecurringExpense.id == recurring_id, models.RecurringExpense.owner_id == user.id
    ).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    return r


@router.get("/", response_model=list[schemas.RecurringOut])
def list_recurring(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    materialize_due(db, user)
    return db.query(models.RecurringExpense).filter(models.RecurringExpense.owner_id == user.id)\
        .order_by(models.RecurringExpense.next_date).all()


@router.post("/", response_model=schemas.RecurringOut, status_code=201)
def create_recurring(body: schemas.RecurringCreate, db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
    r = models.RecurringExpense(
        owner_id=user.id, title=body.title, amount=body.amount, category=body.category,
        notes=body.notes or "", frequency=body.frequency,
        anchor_day=body.start_date.day, next_date=body.start_date,
    )
    db.add(r)
    db.commit()
    materialize_due(db, user)  # back-fill if the start date is today or in the past
    db.refresh(r)
    return r


@router.patch("/{recurring_id}", response_model=schemas.RecurringOut)
def update_recurring(recurring_id: int, body: schemas.RecurringUpdate, db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
    r = _get_owned(db, user, recurring_id)
    resuming = body.active is True and not r.active
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(r, field, value)
    if resuming:
        # skip the time it was paused instead of back-filling it
        today = date.today()
        while r.next_date < today:
            r.next_date = advance(r.next_date, r.frequency, r.anchor_day)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{recurring_id}", status_code=204)
def delete_recurring(recurring_id: int, db: Session = Depends(get_db),
                     user: models.User = Depends(get_current_user)):
    db.delete(_get_owned(db, user, recurring_id))
    db.commit()
