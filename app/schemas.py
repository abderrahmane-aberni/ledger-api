from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TransactionType(str, Enum):
    income = "income"
    expense = "expense"


# ---- auth ----
class UserCreate(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- categories ----
class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ---- transactions ----
class TransactionCreate(BaseModel):
    amount: float
    type: TransactionType
    description: Optional[str] = None
    category_id: Optional[int] = None


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    description: Optional[str] = None
    category_id: Optional[int] = None


class TransactionOut(BaseModel):
    id: int
    amount: float
    type: TransactionType
    description: Optional[str] = None
    date: datetime
    category_id: Optional[int] = None

    class Config:
        from_attributes = True


# ---- budgets ----
class BudgetCreate(BaseModel):
    category_id: int
    monthly_limit: float


class BudgetOut(BaseModel):
    id: int
    category_id: int
    monthly_limit: float

    class Config:
        from_attributes = True


# ---- reports ----
class CategoryBreakdownItem(BaseModel):
    category_id: Optional[int]
    category_name: Optional[str]
    total: float


class MonthlySummaryOut(BaseModel):
    year: int
    month: int
    total_income: float
    total_expense: float
    net: float


class BudgetAlertOut(BaseModel):
    category_id: int
    category_name: str
    monthly_limit: float
    spent: float
    percent_used: float
    over_budget: bool


class RangeSummaryOut(BaseModel):
    range: str
    start_date: datetime
    end_date: datetime
    total_income: float
    total_expense: float
    net: float
    category_breakdown: list[CategoryBreakdownItem]
