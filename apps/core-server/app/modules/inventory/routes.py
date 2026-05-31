from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.inventory.models import InventorySetting, Product
from app.modules.inventory.schemas import ProductRead

router = APIRouter()


@router.get("/products", response_model=list[ProductRead])
def list_products(
    status: str | None = None,
    product_type: str | None = None,
    product_status: str | None = None,
    manage_stock: bool | None = None,
    search: str | None = Query(default=None, description="Search product name, SKU, WooCommerce product ID, or variation ID"),
    db: Session = Depends(get_db),
):
    statement = select(Product)
    if status:
        statement = statement.where(Product.inventory_status == status)
    if product_type:
        statement = statement.where(Product.product_type == product_type)
    if product_status:
        statement = statement.where(Product.product_status == product_status)
    if manage_stock is not None:
        statement = statement.where(Product.manage_stock == manage_stock)
    if search:
        numeric = int(search) if search.isdigit() else -1
        statement = statement.where(or_(
            Product.product_name.ilike(f"%{search}%"),
            Product.sku.ilike(f"%{search}%"),
            Product.woocommerce_product_id == numeric,
            Product.woocommerce_variation_id == numeric,
        ))
    return db.scalars(statement.order_by(Product.product_name).limit(100)).all()


@router.get("/all-products", response_model=list[ProductRead])
def all_products(db: Session = Depends(get_db)):
    return db.scalars(select(Product).order_by(Product.product_name).limit(250)).all()


@router.get("/summary")
def inventory_summary(db: Session = Depends(get_db)) -> dict[str, int]:
    products = db.scalars(select(Product)).all()
    counts: dict[str, int] = {}
    for product in products:
        counts[product.inventory_status.value] = counts.get(product.inventory_status.value, 0) + 1
    counts["all_products"] = len(products)
    return counts


@router.get("/settings")
def inventory_settings(db: Session = Depends(get_db)) -> dict[str, object]:
    rows = db.scalars(select(InventorySetting)).all()
    values = {row.key: row.value for row in rows}
    values.setdefault("default_low_stock_threshold", 2)
    values.setdefault("old_out_of_stock_hide_after_days", 30)
    values.setdefault("category_thresholds", {})
    values.setdefault("product_thresholds", {})
    values.setdefault("exclusions", [])
    values.setdefault("snoozes", [])
    return values
