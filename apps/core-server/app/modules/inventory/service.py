from datetime import datetime, timedelta, timezone
import hashlib
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.modules.inventory.models import InventoryStatus, Product


class InventoryAnalyzer:
    """Inventory status classifier and duplicate-alert state helper."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    def classify(self, product: Product) -> InventoryStatus:
        if product.excluded:
            return InventoryStatus.ignored
        if product.snoozed_until and product.snoozed_until > datetime.now(timezone.utc):
            return InventoryStatus.snoozed
        if not product.manage_stock or product.stock_quantity is None:
            return InventoryStatus.invalid_stock_config
        if product.stock_quantity <= 0:
            if product.out_of_stock_since and product.out_of_stock_since <= datetime.now(timezone.utc) - timedelta(days=self.settings.inventory_old_oos_days):
                return InventoryStatus.old_out_of_stock
            return InventoryStatus.out_of_stock
        threshold = product.threshold_override or self.settings.inventory_low_stock_threshold
        if product.stock_quantity <= threshold:
            return InventoryStatus.low_stock
        return InventoryStatus.normal

    @staticmethod
    def status_hash(product: Product, status: InventoryStatus) -> str:
        payload = f"{product.site_id}:{product.product_id}:{product.variation_id}:{product.stock_quantity}:{status}"
        return hashlib.sha256(payload.encode()).hexdigest()
