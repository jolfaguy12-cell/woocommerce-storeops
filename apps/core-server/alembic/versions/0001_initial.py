"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

inventory_status = postgresql.ENUM("normal", "low_stock", "out_of_stock", "old_out_of_stock", "back_in_stock", "ignored", "snoozed", "invalid_stock_config", name="inventorystatus", create_type=False)
user_role = postgresql.ENUM("super_admin", "inventory_manager", "sales_manager", "readonly_viewer", "accountant", "purchase_manager", "supplier_manager", name="builtinrole", create_type=False)
audit_action = postgresql.ENUM("user_created", "user_updated", "user_deleted", "user_deactivated", "login_success", "login_failed", "role_changed", "permissions_changed", name="auditaction", create_type=False)


def upgrade() -> None:
    inventory_status.create(op.get_bind(), checkfirst=True)
    user_role.create(op.get_bind(), checkfirst=True)
    audit_action.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("permissions", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("target_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("details", sa.JSON()),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "inventory_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.String(120), nullable=False),
        sa.Column("woocommerce_product_id", sa.Integer(), nullable=False),
        sa.Column("woocommerce_variation_id", sa.Integer()),
        sa.Column("parent_woocommerce_product_id", sa.Integer()),
        sa.Column("product_type", sa.String(60), nullable=False),
        sa.Column("product_status", sa.String(60), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("variation_attributes", sa.JSON()),
        sa.Column("sku", sa.String(120)),
        sa.Column("stock_quantity", sa.Integer()),
        sa.Column("stock_status", sa.String(60), nullable=False),
        sa.Column("manage_stock", sa.Boolean(), nullable=False),
        sa.Column("category_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("category_names", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("product_edit_url", sa.Text()),
        sa.Column("date_created", sa.DateTime(timezone=True)),
        sa.Column("date_modified", sa.DateTime(timezone=True)),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("inventory_status", inventory_status, nullable=False),
        sa.Column("out_of_stock_since", sa.DateTime(timezone=True)),
        sa.Column("snoozed_until", sa.DateTime(timezone=True)),
        sa.Column("excluded", sa.Boolean(), nullable=False),
        sa.Column("threshold_override", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("site_id", "woocommerce_product_id", "woocommerce_variation_id", name="uq_inventory_product_identity"),
    )
    op.create_table("inventory_alert_states", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory_products.id", ondelete="CASCADE")), sa.Column("last_alert_type", sa.String(80)), sa.Column("last_stock_value", sa.Integer()), sa.Column("last_status_hash", sa.String(128)), sa.Column("last_alerted_at", sa.DateTime(timezone=True)))
    op.create_table("inventory_thresholds", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("scope", sa.String(40), nullable=False), sa.Column("scope_value", sa.String(255), nullable=False), sa.Column("threshold", sa.Integer(), nullable=False))
    op.create_table("inventory_settings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("key", sa.String(120), nullable=False), sa.Column("value", sa.JSON(), nullable=False, server_default="{}"), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))
    op.create_index("ix_inventory_settings_key", "inventory_settings", ["key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_inventory_settings_key", table_name="inventory_settings")
    op.drop_table("inventory_settings")
    op.drop_table("inventory_thresholds")
    op.drop_table("inventory_alert_states")
    op.drop_table("inventory_products")
    op.drop_table("audit_logs")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")
    audit_action.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
    inventory_status.drop(op.get_bind(), checkfirst=True)
