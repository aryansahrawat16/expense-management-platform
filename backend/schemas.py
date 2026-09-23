from datetime import date as Date, datetime
from typing import Annotated, Literal, Optional
from pydantic import AfterValidator, BaseModel, EmailStr, Field, field_validator
from categories import CATEGORIES

Frequency = Literal["weekly", "monthly", "yearly"]


def _check_category(value: str) -> str:
    if value not in CATEGORIES:
        raise ValueError(f"category must be one of: {', '.join(CATEGORIES)}")
    return value


Category = Annotated[str, AfterValidator(_check_category)]


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6, max_length=72)


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0, le=1_000_000)
    category: Category
    date: Date
    notes: Optional[str] = Field("", max_length=1000)


class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, gt=0, le=1_000_000)
    category: Optional[Category] = None
    date: Optional[Date] = None
    notes: Optional[str] = Field(None, max_length=1000)


class ExpenseOut(BaseModel):
    id: int
    title: str
    amount: float
    category: str
    date: Date
    notes: str
    owner_id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class CategorySummary(BaseModel):
    category: str
    total: float
    count: int


class DashboardStats(BaseModel):
    total_spent: float
    total_this_month: float
    total_expenses: int
    category_breakdown: list[CategorySummary]


class BudgetIn(BaseModel):
    category: Category
    monthly_limit: float = Field(gt=0, le=1_000_000)


class BudgetStatus(BaseModel):
    id: int
    category: str
    monthly_limit: float
    spent: float
    remaining: float
    percent: float
    status: Literal["ok", "warning", "over"]


class MonthTotal(BaseModel):
    month: str
    total: float


class CategoryChange(BaseModel):
    category: str
    this_month: float
    last_month: float
    change_pct: Optional[float]


class Trends(BaseModel):
    months: list[MonthTotal]
    this_month_total: float
    last_month_total: float
    change_pct: Optional[float]
    projected_month_total: float
    categories: list[CategoryChange]


class RecurringCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: float = Field(gt=0, le=1_000_000)
    category: Category
    notes: Optional[str] = Field("", max_length=1000)
    frequency: Frequency
    start_date: Date

    @field_validator("start_date")
    @classmethod
    def not_too_old(cls, v: Date) -> Date:
        if (Date.today() - v).days > 366:
            raise ValueError("start_date can be at most one year in the past")
        return v


class RecurringUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, gt=0, le=1_000_000)
    category: Optional[Category] = None
    notes: Optional[str] = Field(None, max_length=1000)
    active: Optional[bool] = None


class RecurringOut(BaseModel):
    id: int
    title: str
    amount: float
    category: str
    notes: str
    frequency: Frequency
    next_date: Date
    active: bool
    model_config = {"from_attributes": True}


class ImportRow(BaseModel):
    title: str
    amount: float
    date: Date
    category: str
    category_source: Literal["history", "keyword", "default"]
    duplicate: bool


class ImportPreview(BaseModel):
    rows: list[ImportRow]
    skipped: int
    detected_format: str


class ImportCommit(BaseModel):
    rows: list[ExpenseCreate] = Field(max_length=2000)


class ImportResult(BaseModel):
    created: int


class ReceiptScan(BaseModel):
    title: str
    amount: float
    date: Optional[Date]
    category: str
    notes: str
