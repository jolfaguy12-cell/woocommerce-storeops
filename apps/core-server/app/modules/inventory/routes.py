from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.inventory.models import Product
from app.modules.inventory.schemas import ProductRead

router = APIRouter()


@router.get("/products", response_model=list[ProductRead])
def list_products(status: str | None = None, db: Session = Depends(get_db)):
    statement = select(Product).limit(100)
    if status:
        statement = select(Product).where(Product.inventory_status == status).limit(100)
    return db.scalars(statement).all()


@router.get("/summary")
def inventory_summary(db: Session = Depends(get_db)) -> dict[str, int]:
    products = db.scalars(select(Product)).all()
    counts: dict[str, int] = {}
    for product in products:
        counts[product.inventory_status.value] = counts.get(product.inventory_status.value, 0) + 1
    return counts
