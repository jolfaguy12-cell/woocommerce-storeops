from fastapi import APIRouter, Depends, Query
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import require_permission
from app.modules.inventory.models import Product
from app.modules.inventory.schemas import ProductRead
from app.modules.users.models import User

router = APIRouter()

SORT_COLUMNS = {
    "product_name": Product.product_name,
    "sku": Product.sku,
    "stock_quantity": Product.stock_quantity,
    "last_synced_at": Product.last_synced_at,
    "woocommerce_product_id": Product.woocommerce_product_id,
}


@router.get("")
def list_products(
    search: str | None = None,
    product_type: str | None = None,
    product_status: str | None = None,
    stock_status: str | None = None,
    manage_stock: bool | None = None,
    sku: str | None = None,
    woocommerce_product_id: int | None = None,
    woocommerce_variation_id: int | None = None,
    parent_woocommerce_product_id: int | None = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    sort_by: str = "product_name",
    sort_dir: str = "asc",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("products.view")),
):
    statement = select(Product)
    if search:
        numeric = int(search) if search.isdigit() else -1
        statement = statement.where(or_(Product.product_name.ilike(f"%{search}%"), Product.sku.ilike(f"%{search}%"), Product.woocommerce_product_id == numeric, Product.woocommerce_variation_id == numeric))
    if product_type:
        statement = statement.where(Product.product_type == product_type)
    if product_status:
        statement = statement.where(Product.product_status == product_status)
    if stock_status:
        statement = statement.where(Product.stock_status == stock_status)
    if manage_stock is not None:
        statement = statement.where(Product.manage_stock == manage_stock)
    if sku:
        statement = statement.where(Product.sku == sku)
    if woocommerce_product_id is not None:
        statement = statement.where(Product.woocommerce_product_id == woocommerce_product_id)
    if woocommerce_variation_id is not None:
        statement = statement.where(Product.woocommerce_variation_id == woocommerce_variation_id)
    if parent_woocommerce_product_id is not None:
        statement = statement.where(Product.parent_woocommerce_product_id == parent_woocommerce_product_id)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    sort_column = SORT_COLUMNS.get(sort_by, Product.product_name)
    statement = statement.order_by(desc(sort_column) if sort_dir == "desc" else asc(sort_column)).offset((page - 1) * per_page).limit(per_page)
    items = db.scalars(statement).all()
    return {"total": total, "page": page, "per_page": per_page, "items": [ProductRead.model_validate(item).model_dump(mode="json") for item in items]}
