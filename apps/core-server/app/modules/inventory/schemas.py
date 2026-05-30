from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProductSyncPayload(BaseModel):
    site_id: str = "default"
    product_id: int
    variation_id: int | None = None
    parent_product_id: int | None = None
    name: str
    variation_attributes: dict | None = None
    sku: str | None = None
    stock_quantity: int | None = None
    stock_status: str
    manage_stock: bool
    category: str | None = None
    product_edit_url: str | None = None
    last_modified_at: datetime | None = None


class ProductRead(ProductSyncPayload):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inventory_status: str
