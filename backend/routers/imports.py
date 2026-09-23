from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from auth import get_current_user
from categories import categorize_by_keywords
from database import get_db
from importer import CSVFormatError, parse_bank_csv
import models, schemas

router = APIRouter(prefix="/import", tags=["import"])

MAX_BYTES = 2 * 1024 * 1024


def decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


@router.post("/preview", response_model=schemas.ImportPreview)
async def preview(file: UploadFile = File(...), db: Session = Depends(get_db),
                  user: models.User = Depends(get_current_user)):
    raw = await file.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 2 MB.")
    try:
        parsed, skipped, fmt = parse_bank_csv(decode(raw))
    except CSVFormatError as e:
        raise HTTPException(status_code=422, detail=str(e))

    existing = db.query(models.Expense.title, models.Expense.amount, models.Expense.date, models.Expense.category)\
        .filter(models.Expense.owner_id == user.id).order_by(models.Expense.date).all()
    # ordered by date so the most recent category for a merchant wins
    learned = {title.lower(): category for title, _, _, category in existing}
    seen = {(title.lower(), round(amount, 2), d) for title, amount, d, _ in existing}

    rows = []
    for p in parsed:
        if p.title.lower() in learned:
            category, source = learned[p.title.lower()], "history"
        elif (kw := categorize_by_keywords(p.title)):
            category, source = kw, "keyword"
        else:
            category, source = "Other", "default"
        rows.append(schemas.ImportRow(
            title=p.title, amount=p.amount, date=p.date, category=category, category_source=source,
            duplicate=(p.title.lower(), p.amount, p.date) in seen,
        ))
    return schemas.ImportPreview(rows=rows, skipped=skipped, detected_format=fmt)


@router.post("/commit", response_model=schemas.ImportResult, status_code=201)
def commit(body: schemas.ImportCommit, db: Session = Depends(get_db),
           user: models.User = Depends(get_current_user)):
    db.add_all(models.Expense(**row.model_dump(), owner_id=user.id) for row in body.rows)
    db.commit()
    return schemas.ImportResult(created=len(body.rows))
