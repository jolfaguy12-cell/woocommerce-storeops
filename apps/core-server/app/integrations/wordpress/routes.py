from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import verify_wordpress_signature
from app.db.session import get_db
from app.modules.inventory.schemas import ProductSyncPayload
from app.modules.inventory.upsert import upsert_products

router = APIRouter(dependencies=[Depends(verify_wordpress_signature)])


@router.post("/products/changed")
def receive_changed_products(payload: list[ProductSyncPayload], db: Session = Depends(get_db)) -> dict[str, int]:
    return upsert_products(payload, db)


@router.post("/products/full-sync")
def receive_full_product_sync(payload: list[ProductSyncPayload], db: Session = Depends(get_db)) -> dict[str, int]:
    return upsert_products(payload, db)
