from __future__ import annotations

DEFAULT_SETTINGS: list[dict] = [
    # General
    {"key": "store_name", "group": "general", "label": "Store name", "value_type": "string", "default_value": "WooCommerce StoreOps", "description": "Display name used inside the admin panel."},
    {"key": "admin_email", "group": "general", "label": "Admin email", "value_type": "string", "default_value": "admin@example.com", "description": "Primary administrative contact email."},
    {"key": "environment_label", "group": "general", "label": "Environment label", "value_type": "string", "default_value": "Production", "description": "Label shown in the admin header."},
    {"key": "default_timezone", "group": "general", "label": "Default timezone", "value_type": "string", "default_value": "Asia/Tehran"},
    {"key": "date_display_mode", "group": "general", "label": "Date display mode", "value_type": "string", "default_value": "jalali", "options": ["gregorian", "jalali"]},
    {"key": "dashboard_language", "group": "general", "label": "Dashboard language", "value_type": "string", "default_value": "en", "options": ["en", "fa"]},
    # WordPress connector
    {"key": "wordpress_base_url", "group": "wordpress_connector", "label": "WordPress base URL", "value_type": "string", "default_value": ""},
    {"key": "connector_status", "group": "wordpress_connector", "label": "Connector status", "value_type": "string", "default_value": "not_configured", "is_editable": False},
    {"key": "last_successful_connection_at", "group": "wordpress_connector", "label": "Last successful connection", "value_type": "string", "default_value": None, "is_editable": False},
    {"key": "last_failed_connection_at", "group": "wordpress_connector", "label": "Last failed connection", "value_type": "string", "default_value": None, "is_editable": False},
    {"key": "connector_timeout_seconds", "group": "wordpress_connector", "label": "Connector timeout seconds", "value_type": "integer", "default_value": 20, "validation_rules": {"min": 1, "max": 120}},
    {"key": "connector_retry_count", "group": "wordpress_connector", "label": "Connector retry count", "value_type": "integer", "default_value": 3, "validation_rules": {"min": 0, "max": 10}},
    # Sync
    {"key": "full_sync_batch_size", "group": "sync", "label": "Full sync batch size", "value_type": "integer", "default_value": 50, "validation_rules": {"min": 1, "max": 200}},
    {"key": "full_sync_daily_time", "group": "sync", "label": "Full sync daily time", "value_type": "string", "default_value": "03:00", "validation_rules": {"format": "HH:MM"}},
    {"key": "changed_sync_interval_seconds", "group": "sync", "label": "Changed sync interval seconds", "value_type": "integer", "default_value": 60, "validation_rules": {"min": 30, "max": 86400}},
    {"key": "post_order_sync_delay_seconds", "group": "sync", "label": "Post-order sync delay seconds", "value_type": "integer", "default_value": 60, "validation_rules": {"min": 0, "max": 3600}},
    {"key": "sync_request_timeout_seconds", "group": "sync", "label": "Sync request timeout seconds", "value_type": "integer", "default_value": 20, "validation_rules": {"min": 1, "max": 300}},
    {"key": "max_parallel_sync_jobs", "group": "sync", "label": "Max parallel sync jobs", "value_type": "integer", "default_value": 1, "validation_rules": {"min": 1, "max": 5}},
    {"key": "prevent_parallel_full_sync", "group": "sync", "label": "Prevent parallel full sync", "value_type": "boolean", "default_value": True},
    {"key": "sync_retry_count", "group": "sync", "label": "Sync retry count", "value_type": "integer", "default_value": 3, "validation_rules": {"min": 0, "max": 10}},
    {"key": "sync_retry_delay_seconds", "group": "sync", "label": "Sync retry delay seconds", "value_type": "integer", "default_value": 2, "validation_rules": {"min": 0, "max": 60}},
    # Inventory
    {"key": "default_low_stock_threshold", "group": "inventory", "label": "Default low-stock threshold", "value_type": "integer", "default_value": 2, "validation_rules": {"min": 0, "max": 100000}},
    {"key": "old_out_of_stock_hide_after_days", "group": "inventory", "label": "Old out-of-stock hide-after days", "value_type": "integer", "default_value": 30, "validation_rules": {"min": 1, "max": 3650}},
    {"key": "include_draft_products", "group": "inventory", "label": "Include draft products", "value_type": "boolean", "default_value": True},
    {"key": "include_private_products", "group": "inventory", "label": "Include private products", "value_type": "boolean", "default_value": True},
    {"key": "include_manage_stock_disabled_products", "group": "inventory", "label": "Include manage-stock-disabled products", "value_type": "boolean", "default_value": True},
    {"key": "enable_product_exclusions", "group": "inventory", "label": "Enable product exclusions", "value_type": "boolean", "default_value": True},
    {"key": "enable_product_snooze", "group": "inventory", "label": "Enable product snooze", "value_type": "boolean", "default_value": True},
    # Notifications
    {"key": "telegram_enabled", "group": "notifications", "label": "Telegram enabled", "value_type": "boolean", "default_value": False},
    {"key": "notification_grouping_enabled", "group": "notifications", "label": "Notification grouping enabled", "value_type": "boolean", "default_value": True},
    {"key": "duplicate_alert_prevention_enabled", "group": "notifications", "label": "Duplicate alert prevention enabled", "value_type": "boolean", "default_value": True},
    {"key": "back_in_stock_alert_enabled", "group": "notifications", "label": "Back-in-stock alert enabled", "value_type": "boolean", "default_value": True},
    # Reports
    {"key": "default_report_date_mode", "group": "reports", "label": "Default report date mode", "value_type": "string", "default_value": "jalali", "options": ["gregorian", "jalali"]},
    {"key": "default_report_template", "group": "reports", "label": "Default report template", "value_type": "string", "default_value": "daily_inventory_summary"},
    {"key": "report_store_name", "group": "reports", "label": "Report store name", "value_type": "string", "default_value": "WooCommerce StoreOps"},
    {"key": "report_logo_path", "group": "reports", "label": "Report logo path", "value_type": "string", "default_value": ""},
    {"key": "include_sku_by_default", "group": "reports", "label": "Include SKU by default", "value_type": "boolean", "default_value": True},
    {"key": "include_variations_by_default", "group": "reports", "label": "Include variations by default", "value_type": "boolean", "default_value": True},
    {"key": "include_product_edit_link_by_default", "group": "reports", "label": "Include product edit link by default", "value_type": "boolean", "default_value": True},
    # Security
    {"key": "login_max_attempts", "group": "security", "label": "Login max attempts", "value_type": "integer", "default_value": 5, "validation_rules": {"min": 1, "max": 20}},
    {"key": "login_lockout_minutes", "group": "security", "label": "Login lockout minutes", "value_type": "integer", "default_value": 10, "validation_rules": {"min": 1, "max": 1440}},
    {"key": "session_lifetime_minutes", "group": "security", "label": "Session lifetime minutes", "value_type": "integer", "default_value": 60, "validation_rules": {"min": 5, "max": 10080}},
    {"key": "password_min_length", "group": "security", "label": "Password minimum length", "value_type": "integer", "default_value": 10, "validation_rules": {"min": 8, "max": 128}},
    {"key": "require_strong_passwords", "group": "security", "label": "Require strong passwords", "value_type": "boolean", "default_value": True},
    {"key": "audit_log_retention_days", "group": "security", "label": "Audit log retention days", "value_type": "integer", "default_value": 365, "validation_rules": {"min": 30, "max": 3650}},
    # System
    {"key": "log_level", "group": "system", "label": "Log level", "value_type": "string", "default_value": "INFO", "options": ["DEBUG", "INFO", "WARNING", "ERROR"]},
    {"key": "app_internal_port", "group": "system", "label": "App internal port", "value_type": "integer", "default_value": 8088, "validation_rules": {"min": 1024, "max": 65535}},
    {"key": "maintenance_mode", "group": "system", "label": "Maintenance mode", "value_type": "boolean", "default_value": False},
    {"key": "enable_debug_tools", "group": "system", "label": "Enable debug tools", "value_type": "boolean", "default_value": False},
]
