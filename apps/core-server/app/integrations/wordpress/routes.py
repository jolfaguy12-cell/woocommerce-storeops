from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.core.security import verify_wordpress_signature
from app.db.session import get_db
from app.modules.inventory.models import Product
from app.modules.inventory.schemas import ProductSyncPayload
from app.modules.inventory.service import InventoryAnalyzer

router = APIRouter(dependencies=[Depends(verify_wordpress_signature)])


def upsert_products(payload: list[ProductSyncPayload], db: Session) -> int:
    analyzer = InventoryAnalyzer(db)
    upserted = 0
    for item in payload:
        try:
            data = item.normalized()
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
        data["last_synced_at"] = data.get("last_synced_at") or utc_now()
        product = db.scalar(select(Product).where(
            Product.site_id == data["site_id"],
            Product.woocommerce_product_id == data["woocommerce_product_id"],
            Product.woocommerce_variation_id == data["woocommerce_variation_id"],
        ))
        if product is None:
            product = Product(**data)
            db.add(product)
        else:
            for key, value in data.items():
                setattr(product, key, value)
        if product.stock_quantity is not None and product.stock_quantity <= 0 and product.out_of_stock_since is None:
            product.out_of_stock_since = utc_now()
        if product.stock_quantity is not None and product.stock_quantity > 0:
            product.out_of_stock_since = None
        product.inventory_status = analyzer.classify(product)
        upserted += 1
    db.commit()
    return upserted


@router.post("/products/changed")
def receive_changed_products(payload: list[ProductSyncPayload], db: Session = Depends(get_db)) -> dict[str, int]:
    return {"upserted": upsert_products(payload, db)}


@router.post("/products/full-sync")
def receive_full_product_sync(payload: list[ProductSyncPayload], db: Session = Depends(get_db)) -> dict[str, int]:
    return {"upserted": upsert_products(payload, db)}
