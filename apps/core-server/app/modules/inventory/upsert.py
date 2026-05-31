from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.datetime_utils import utc_now
from app.modules.inventory.models import Product
from app.modules.inventory.schemas import ProductSyncPayload
from app.modules.inventory.service import InventoryAnalyzer


def upsert_products(payload: list[ProductSyncPayload], db: Session) -> dict[str, int]:
    analyzer = InventoryAnalyzer(db)
    stats = {"processed_items": 0, "created_items": 0, "updated_items": 0, "failed_items": 0}
    for item in payload:
        try:
            data = item.normalized()
            data["last_synced_at"] = data.get("last_synced_at") or utc_now()
            product = db.scalar(select(Product).where(
                Product.site_id == data["site_id"],
                Product.woocommerce_product_id == data["woocommerce_product_id"],
                Product.woocommerce_variation_id == data["woocommerce_variation_id"],
            ))
            if product is None:
                product = Product(**data)
                db.add(product)
                stats["created_items"] += 1
            else:
                for key, value in data.items():
                    setattr(product, key, value)
                stats["updated_items"] += 1
            if product.stock_quantity is not None and product.stock_quantity <= 0 and product.out_of_stock_since is None:
                product.out_of_stock_since = utc_now()
            if product.stock_quantity is not None and product.stock_quantity > 0:
                product.out_of_stock_since = None
            product.inventory_status = analyzer.classify(product)
            stats["processed_items"] += 1
        except Exception:
            stats["failed_items"] += 1
            raise
    db.commit()
    return stats
