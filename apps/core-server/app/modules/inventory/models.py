import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class InventoryStatus(str, enum.Enum):
    normal = "normal"
    low_stock = "low_stock"
    out_of_stock = "out_of_stock"
    old_out_of_stock = "old_out_of_stock"
    back_in_stock = "back_in_stock"
    ignored = "ignored"
    snoozed = "snoozed"
    invalid_stock_config = "invalid_stock_config"


class Product(Base):
    __tablename__ = "inventory_products"
    __table_args__ = (UniqueConstraint("site_id", "product_id", "variation_id", name="uq_inventory_product_identity"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[str] = mapped_column(String(120), index=True, default="default")
    product_id: Mapped[int] = mapped_column(Integer, index=True)
    variation_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    parent_product_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    variation_attributes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    sku: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stock_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stock_status: Mapped[str] = mapped_column(String(60), index=True)
    manage_stock: Mapped[bool] = mapped_column(Boolean, default=False)
    product_edit_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    inventory_status: Mapped[InventoryStatus] = mapped_column(Enum(InventoryStatus), default=InventoryStatus.normal, index=True)
    out_of_stock_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    snoozed_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    excluded: Mapped[bool] = mapped_column(Boolean, default=False)
    threshold_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    alerts: Mapped[list["InventoryAlertState"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class InventoryAlertState(Base):
    __tablename__ = "inventory_alert_states"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("inventory_products.id", ondelete="CASCADE"), index=True)
    last_alert_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_stock_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_status_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_alerted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    product: Mapped[Product] = relationship(back_populates="alerts")


class InventoryThreshold(Base):
    __tablename__ = "inventory_thresholds"

    id: Mapped[int] = mapped_column(primary_key=True)
    scope: Mapped[str] = mapped_column(String(40), index=True)  # global, category, product
    scope_value: Mapped[str] = mapped_column(String(255), default="global", index=True)
    threshold: Mapped[int] = mapped_column(Integer, default=2)
