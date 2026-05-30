from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_wordpress_signature
from app.db.session import get_db
from app.modules.inventory.models import Product
from app.modules.inventory.schemas import ProductSyncPayload
from app.modules.inventory.service import InventoryAnalyzer

router = APIRouter(dependencies=[Depends(verify_wordpress_signature)])


@router.post("/products/changed")
def receive_changed_products(payload: list[ProductSyncPayload], db: Session = Depends(get_db)) -> dict[str, int]:
    analyzer = InventoryAnalyzer(db)
    upserted = 0
    for item in payload:
        product = db.scalar(select(Product).where(
            Product.site_id == item.site_id,
            Product.product_id == item.product_id,
            Product.variation_id == item.variation_id,
        ))
        if product is None:
            product = Product(**item.model_dump())
            db.add(product)
        else:
            for key, value in item.model_dump().items():
                setattr(product, key, value)
        if item.stock_quantity is not None and item.stock_quantity <= 0 and product.out_of_stock_since is None:
            product.out_of_stock_since = datetime.now(timezone.utc)
        if item.stock_quantity is not None and item.stock_quantity > 0:
            product.out_of_stock_since = None
        product.inventory_status = analyzer.classify(product)
        upserted += 1
    db.commit()
    return {"upserted": upserted}
