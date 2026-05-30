from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ProductSyncPayload(BaseModel):
    site_id: str = "default"
    woocommerce_product_id: int | None = None
    woocommerce_variation_id: int | None = None
    parent_woocommerce_product_id: int | None = None
    product_type: str = "simple"
    product_status: str = "unknown"
    product_name: str | None = None
    variation_attributes: dict | None = None
    sku: str | None = None
    stock_quantity: int | None = None
    stock_status: str
    manage_stock: bool
    category_ids: list[int] = Field(default_factory=list)
    category_names: list[str] = Field(default_factory=list)
    product_edit_url: str | None = None
    date_created: datetime | None = None
    date_modified: datetime | None = None
    last_synced_at: datetime | None = None

    # Backwards-compatible input aliases accepted from earlier connector payloads.
    product_id: int | None = None
    variation_id: int | None = None
    parent_product_id: int | None = None
    name: str | None = None
    category: str | None = None
    last_modified_at: datetime | None = None

    def normalized(self) -> dict:
        data = self.model_dump(exclude={"product_id", "variation_id", "parent_product_id", "name", "category", "last_modified_at"})
        data["woocommerce_product_id"] = self.woocommerce_product_id or self.product_id
        data["woocommerce_variation_id"] = self.woocommerce_variation_id if self.woocommerce_variation_id is not None else self.variation_id
        data["parent_woocommerce_product_id"] = self.parent_woocommerce_product_id if self.parent_woocommerce_product_id is not None else self.parent_product_id
        data["product_name"] = self.product_name or self.name or "Unnamed product"
        if not data["category_names"] and self.category:
            data["category_names"] = [part.strip() for part in self.category.split(",") if part.strip()]
        data["date_modified"] = self.date_modified or self.last_modified_at
        if data["woocommerce_product_id"] is None:
            raise ValueError("woocommerce_product_id is required")
        return data


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    site_id: str
    woocommerce_product_id: int
    woocommerce_variation_id: int | None
    parent_woocommerce_product_id: int | None
    product_type: str
    product_status: str
    product_name: str
    variation_attributes: dict | None
    sku: str | None
    stock_quantity: int | None
    stock_status: str
    manage_stock: bool
    category_ids: list[int]
    category_names: list[str]
    product_edit_url: str | None
    date_created: datetime | None
    date_modified: datetime | None
    last_synced_at: datetime | None
    inventory_status: str
