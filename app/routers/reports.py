from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/monthly-summary", response_model=schemas.MonthlySummaryOut)
def monthly_summary(
    year: int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    totals = (
        db.query(models.Transaction.type, func.sum(models.Transaction.amount))
        .filter(
            models.Transaction.user_id == current_user.id,
            extract("year", models.Transaction.date) == year,
            extract("month", models.Transaction.date) == month,
        )
        .group_by(models.Transaction.type)
        .all()
    )
    income = next((float(t) for ty, t in totals if ty == models.TransactionType.income), 0.0)
    expense = next((float(t) for ty, t in totals if ty == models.TransactionType.expense), 0.0)
    return schemas.MonthlySummaryOut(year=year, month=month, total_income=income, total_expense=expense, net=income - expense)


@router.get("/category-breakdown", response_model=list[schemas.CategoryBreakdownItem])
def category_breakdown(
    year: int = Query(default=None),
    month: int = Query(default=None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month

    rows = (
        db.query(
            models.Category.id,
            models.Category.name,
            func.coalesce(func.sum(models.Transaction.amount), 0.0),
        )
        .join(models.Transaction, models.Transaction.category_id == models.Category.id)
        .filter(
            models.Category.user_id == current_user.id,
            models.Transaction.type == models.TransactionType.expense,
            extract("year", models.Transaction.date) == year,
            extract("month", models.Transaction.date) == month,
        )
        .group_by(models.Category.id, models.Category.name)
        .all()
    )
    return [
        schemas.CategoryBreakdownItem(category_id=cid, category_name=name, total=float(total))
        for cid, name, total in rows
    ]


@router.get("/budget-alerts", response_model=list[schemas.BudgetAlertOut])
def budget_alerts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    budgets = db.query(models.Budget).filter(models.Budget.user_id == current_user.id).all()
    alerts = []
    for budget in budgets:
        spent = (
            db.query(func.coalesce(func.sum(models.Transaction.amount), 0.0))
            .filter(
                models.Transaction.category_id == budget.category_id,
                models.Transaction.user_id == current_user.id,
                models.Transaction.type == models.TransactionType.expense,
                extract("year", models.Transaction.date) == now.year,
                extract("month", models.Transaction.date) == now.month,
            )
            .scalar()
        )
        spent = float(spent or 0.0)
        percent = (spent / budget.monthly_limit * 100) if budget.monthly_limit else 0.0
        alerts.append(
            schemas.BudgetAlertOut(
                category_id=budget.category_id,
                category_name=budget.category.name,
                monthly_limit=budget.monthly_limit,
                spent=spent,
                percent_used=round(percent, 1),
                over_budget=spent > budget.monthly_limit,
            )
        )
    return alerts

RANGE_DAYS = {
    "week": 7,
    "month": 30,
    "3months": 90,
    "3years": 365 * 3,
}


@router.get("/summary", response_model=schemas.RangeSummaryOut)
def range_summary(
    range: str = Query(default="month", pattern="^(week|month|3months|3years)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Rolling-window summary (unlike /monthly-summary, which is pinned to a
    single calendar month) -- powers the frontend's period comparison selector."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=RANGE_DAYS[range])

    totals = (
        db.query(models.Transaction.type, func.sum(models.Transaction.amount))
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.date >= start_date,
            models.Transaction.date <= end_date,
        )
        .group_by(models.Transaction.type)
        .all()
    )
    income = next((float(t) for ty, t in totals if ty == models.TransactionType.income), 0.0)
    expense = next((float(t) for ty, t in totals if ty == models.TransactionType.expense), 0.0)

    rows = (
        db.query(
            models.Category.id,
            models.Category.name,
            func.coalesce(func.sum(models.Transaction.amount), 0.0),
        )
        .join(models.Transaction, models.Transaction.category_id == models.Category.id)
        .filter(
            models.Category.user_id == current_user.id,
            models.Transaction.type == models.TransactionType.expense,
            models.Transaction.date >= start_date,
            models.Transaction.date <= end_date,
        )
        .group_by(models.Category.id, models.Category.name)
        .all()
    )
    breakdown = [
        schemas.CategoryBreakdownItem(category_id=cid, category_name=name, total=float(t))
        for cid, name, t in rows
    ]

    return schemas.RangeSummaryOut(
        range=range,
        start_date=start_date,
        end_date=end_date,
        total_income=income,
        total_expense=expense,
        net=income - expense,
        category_breakdown=breakdown,
    )

