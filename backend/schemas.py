from datetime import date as Date, datetime
from typing import Annotated, Optional
from pydantic import AfterValidator, BaseModel, EmailStr, Field
from categories import CATEGORIES

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
