from fastapi import APIRouter, Depends

from app.config.settings import get_settings
from app.modules.auth.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter()

DASHBOARD_PAGES = [
    "Login", "Main Dashboard", "Modules", "Sync Center", "All Products", "Inventory", "Inventory Report", "Low Stock", "Out of Stock",
    "Old Out of Stock", "Product History", "Inventory Settings", "Queue Monitor", "Connector Status",
    "Telegram Settings", "Report Builder", "Report Templates", "Users & Roles", "Add New User", "Edit User",
    "Role Permissions", "Date & Localization Settings", "Logs", "System Settings", "System Ports / Deployment Notes",
    "Accounting", "Orders", "Purchases", "Suppliers", "Sales Analytics", "Financial Reports",
]

COMING_SOON = {"Accounting", "Orders", "Purchases", "Suppliers", "Sales Analytics", "Financial Reports"}


@router.get("/navigation")
def navigation(current_user: User = Depends(require_permission("dashboard.view"))) -> list[dict[str, str | bool]]:
    permissions = current_user.effective_permissions()
    pages = []
    for page in DASHBOARD_PAGES:
        required = "dashboard.view"
        if page == "Sync Center":
            required = "sync.view"
        if page == "All Products":
            required = "products.view"
        if page in {"Users & Roles", "Add New User", "Edit User"}:
            required = "users.view"
        pages.append({"label": page, "enabled": page not in COMING_SOON and required in permissions})
    return pages


@router.get("/localization")
def localization_settings(current_user: User = Depends(require_permission("settings.view"))) -> dict[str, str | list[str]]:
    settings = get_settings()
    return {
        "date_display_mode": settings.date_display_mode,
        "available_date_display_modes": ["gregorian", "jalali"],
        "timezone": settings.timezone,
        "report_date_format": "jalali" if settings.date_display_mode == "jalali" else "gregorian",
    }


@router.get("/connector-status")
def connector_status(current_user: User = Depends(require_permission("sync.view"))) -> dict[str, str | None]:
    return {
        "wordpress_connector_url": None,
        "last_successful_connection": None,
        "last_failed_connection": None,
        "last_full_sync": None,
        "last_changed_products_sync": None,
        "connection_health": "not_configured",
    }


@router.get("/deployment-notes")
def deployment_notes(current_user: User = Depends(require_permission("settings.view"))) -> dict[str, object]:
    settings = get_settings()
    return {
        "app_host": settings.app_host,
        "app_port": settings.app_port,
        "avoid_ports": [22, 53, 80, 443, 3000, 30303, 8545, 8551, 9000, 3610, 5000, 6363, 9090, 3100, 18550],
        "database_public_exposure": "disabled_by_default",
        "redis_public_exposure": "disabled_by_default",
    }


@router.get("/pages/login")
def login_page() -> dict[str, object]:
    return {
        "page": "Login",
        "endpoint": "/api/v1/auth/login",
        "fields": ["username", "password"],
        "notes": "Frontend should submit credentials and store the HTTP-only session cookie/JWT response securely.",
    }


@router.get("/pages/sync-center")
def sync_center_page(current_user: User = Depends(require_permission("sync.view"))) -> dict[str, object]:
    permissions = current_user.effective_permissions()
    return {
        "page": "Sync Center",
        "cards": ["WordPress connection", "Core Server", "Database", "Redis/Celery"],
        "actions": {
            "run_full_product_sync": "sync.run_full" in permissions,
            "run_changed_products_sync": "sync.run_changed" in permissions,
            "check_wordpress_connection": "sync.view" in permissions,
        },
        "status_endpoint": "/api/v1/sync/status",
        "history_endpoint": "/api/v1/sync/jobs",
        "empty_state": "No sync has run yet.",
    }


@router.get("/pages/all-products")
def all_products_page(current_user: User = Depends(require_permission("products.view"))) -> dict[str, object]:
    return {
        "page": "All Products",
        "endpoint": "/api/v1/products",
        "columns": ["product_name", "product_type", "product_status", "sku", "stock_quantity", "stock_status", "woocommerce_product_id", "woocommerce_variation_id", "parent_woocommerce_product_id", "last_synced_at"],
    }
