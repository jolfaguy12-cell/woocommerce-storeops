"""system settings admin foundation

Revision ID: 0003_system_settings_admin_foundation
Revises: 0002_auth_sync_foundation
Create Date: 2026-05-30
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from app.modules.settings.defaults import DEFAULT_SETTINGS
from sqlalchemy.dialects import postgresql

revision = "0003_system_settings_admin_foundation"
down_revision = "0002_auth_sync_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(160), nullable=False),
        sa.Column("value", sa.JSON(), nullable=True),
        sa.Column("value_type", sa.String(40), nullable=False, server_default="string"),
        sa.Column("group", sa.String(80), nullable=False),
        sa.Column("label", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("default_value", sa.JSON(), nullable=True),
        sa.Column("is_secret", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_editable", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("validation_rules", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("key", name="uq_system_settings_key"),
    )
    op.create_index("ix_system_settings_key", "system_settings", ["key"], unique=True)
    op.create_index("ix_system_settings_group", "system_settings", ["group"])

    settings_table = sa.table(
        "system_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.JSON),
        sa.column("value_type", sa.String),
        sa.column("group", sa.String),
        sa.column("label", sa.String),
        sa.column("description", sa.Text),
        sa.column("default_value", sa.JSON),
        sa.column("is_secret", sa.Boolean),
        sa.column("is_public", sa.Boolean),
        sa.column("is_editable", sa.Boolean),
        sa.column("validation_rules", sa.JSON),
        sa.column("options", sa.JSON),
        sa.column("display_order", sa.Integer),
    )
    op.bulk_insert(settings_table, [
        {
            "key": item["key"],
            "value": item.get("default_value"),
            "value_type": item.get("value_type", "string"),
            "group": item["group"],
            "label": item.get("label", item["key"].replace("_", " ").title()),
            "description": item.get("description"),
            "default_value": item.get("default_value"),
            "is_secret": item.get("is_secret", False),
            "is_public": item.get("is_public", False),
            "is_editable": item.get("is_editable", True),
            "validation_rules": item.get("validation_rules", {}),
            "options": item.get("options"),
            "display_order": item.get("display_order", index),
        }
        for index, item in enumerate(DEFAULT_SETTINGS, start=1)
    ])

    # Keep existing deployments in sync with the expanded permission catalog. Role
    # assignments are refreshed by the app's seed_roles_and_permissions helper.
    bind = op.get_bind()
    permissions = [
        ("products.manage", "products", "Manage synced product metadata"),
        ("notifications.view", "notifications", "View notification settings"),
        ("notifications.manage", "notifications", "Manage notification settings"),
        ("modules.view", "modules", "View modules"),
        ("modules.manage", "modules", "Manage modules"),
    ]
    for code, module, description in permissions:
        bind.execute(sa.text("""
            INSERT INTO permissions (code, module, description)
            VALUES (:code, :module, :description)
            ON CONFLICT (code) DO UPDATE SET module = EXCLUDED.module, description = EXCLUDED.description
        """), {"code": code, "module": module, "description": description})


def downgrade() -> None:
    op.drop_index("ix_system_settings_group", table_name="system_settings")
    op.drop_index("ix_system_settings_key", table_name="system_settings")
    op.drop_table("system_settings")
