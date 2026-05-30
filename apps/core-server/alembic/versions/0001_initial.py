"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

inventory_status = sa.Enum("normal", "low_stock", "out_of_stock", "old_out_of_stock", "back_in_stock", "ignored", "snoozed", "invalid_stock_config", name="inventorystatus")
user_role = sa.Enum("super_admin", "inventory_manager", "sales_manager", "readonly_viewer", "accountant", "purchase_manager", "supplier_manager", name="builtinrole")


def upgrade() -> None:
    inventory_status.create(op.get_bind(), checkfirst=True)
    user_role.create(op.get_bind(), checkfirst=True)
    op.create_table("users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("username", sa.String(150), nullable=False), sa.Column("email", sa.String(255)), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("role", user_role, nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table("inventory_products", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("site_id", sa.String(120), nullable=False), sa.Column("product_id", sa.Integer(), nullable=False), sa.Column("variation_id", sa.Integer()), sa.Column("parent_product_id", sa.Integer()), sa.Column("name", sa.String(255), nullable=False), sa.Column("variation_attributes", sa.JSON()), sa.Column("sku", sa.String(120)), sa.Column("category", sa.String(255)), sa.Column("stock_quantity", sa.Integer()), sa.Column("stock_status", sa.String(60), nullable=False), sa.Column("manage_stock", sa.Boolean(), nullable=False), sa.Column("product_edit_url", sa.Text()), sa.Column("last_modified_at", sa.DateTime(timezone=True)), sa.Column("inventory_status", inventory_status, nullable=False), sa.Column("out_of_stock_since", sa.DateTime(timezone=True)), sa.Column("snoozed_until", sa.DateTime(timezone=True)), sa.Column("excluded", sa.Boolean(), nullable=False), sa.Column("threshold_override", sa.Integer()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()), sa.UniqueConstraint("site_id", "product_id", "variation_id", name="uq_inventory_product_identity"))
    op.create_table("inventory_alert_states", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_products.id", ondelete="CASCADE")), sa.Column("last_alert_type", sa.String(80)), sa.Column("last_stock_value", sa.Integer()), sa.Column("last_status_hash", sa.String(128)), sa.Column("last_alerted_at", sa.DateTime(timezone=True)))
    op.create_table("inventory_thresholds", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("scope", sa.String(40), nullable=False), sa.Column("scope_value", sa.String(255), nullable=False), sa.Column("threshold", sa.Integer(), nullable=False))


def downgrade() -> None:
    op.drop_table("inventory_thresholds")
    op.drop_table("inventory_alert_states")
    op.drop_table("inventory_products")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
    user_role.drop(op.get_bind(), checkfirst=True)
    inventory_status.drop(op.get_bind(), checkfirst=True)
