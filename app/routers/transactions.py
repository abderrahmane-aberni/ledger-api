import csv
import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.deps import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", response_model=schemas.TransactionOut)
def create_transaction(
    tx: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if tx.category_id is not None:
        category = (
            db.query(models.Category)
            .filter(models.Category.id == tx.category_id, models.Category.user_id == current_user.id)
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    new_tx = models.Transaction(
        amount=tx.amount,
        type=tx.type,
        description=tx.description,
        category_id=tx.category_id,
        user_id=current_user.id,
    )
    db.add(new_tx)
    db.commit()
    db.refresh(new_tx)
    return new_tx


@router.get("/", response_model=list[schemas.TransactionOut])
def list_transactions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.date.desc())
        .all()
    )


@router.patch("/{transaction_id}", response_model=schemas.TransactionOut)
def update_transaction(
    transaction_id: int,
    tx_update: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tx = (
        db.query(models.Transaction)
        .filter(models.Transaction.id == transaction_id, models.Transaction.user_id == current_user.id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for field, value in tx_update.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    tx = (
        db.query(models.Transaction)
        .filter(models.Transaction.id == transaction_id, models.Transaction.user_id == current_user.id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(tx)
    db.commit()
    return None


@router.get("/export")
def export_transactions_csv(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    txs = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .order_by(models.Transaction.date.desc())
        .all()
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "amount", "type", "description", "date", "category_id"])
    for tx in txs:
        writer.writerow(
            [tx.id, tx.amount, tx.type.value, tx.description or "", tx.date.isoformat(), tx.category_id or ""]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"},
    )


@router.post("/import")
def import_transactions_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    created = 0
    errors = []
    for i, row in enumerate(reader, start=1):
        try:
            amount = float(row["amount"])
            tx_type = models.TransactionType(row["type"].strip().lower())
            category_id = int(row["category_id"]) if row.get("category_id") else None
            if category_id is not None:
                category = (
                    db.query(models.Category)
                    .filter(models.Category.id == category_id, models.Category.user_id == current_user.id)
                    .first()
                )
                if not category:
                    errors.append(f"Row {i}: category_id {category_id} not found")
                    continue
            new_tx = models.Transaction(
                amount=amount,
                type=tx_type,
                description=row.get("description") or None,
                category_id=category_id,
                user_id=current_user.id,
            )
            db.add(new_tx)
            created += 1
        except (KeyError, ValueError) as e:
            errors.append(f"Row {i}: {e}")
    db.commit()
    return {"created": created, "errors": errors}
