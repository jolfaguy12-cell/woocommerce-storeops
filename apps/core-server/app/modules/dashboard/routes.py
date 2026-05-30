from fastapi import APIRouter

from app.config.settings import get_settings

router = APIRouter()

DASHBOARD_PAGES = [
    "Main Dashboard", "Modules", "All Products", "Inventory", "Inventory Report", "Low Stock", "Out of Stock",
    "Old Out of Stock", "Product History", "Inventory Settings", "Queue Monitor", "Connector Status",
    "Telegram Settings", "Report Builder", "Report Templates", "Users & Roles", "Add New User", "Edit User",
    "Role Permissions", "Date & Localization Settings", "Logs", "System Settings", "System Ports / Deployment Notes",
    "Accounting", "Orders", "Purchases", "Suppliers", "Sales Analytics", "Financial Reports",
]

COMING_SOON = {"Accounting", "Orders", "Purchases", "Suppliers", "Sales Analytics", "Financial Reports"}


@router.get("/navigation")
def navigation() -> list[dict[str, str | bool]]:
    return [{"label": page, "enabled": page not in COMING_SOON} for page in DASHBOARD_PAGES]


@router.get("/localization")
def localization_settings() -> dict[str, str | list[str]]:
    settings = get_settings()
    return {
        "date_display_mode": settings.date_display_mode,
        "available_date_display_modes": ["gregorian", "jalali"],
        "timezone": settings.timezone,
        "report_date_format": "jalali" if settings.date_display_mode == "jalali" else "gregorian",
    }


@router.get("/connector-status")
def connector_status() -> dict[str, str | None]:
    return {
        "wordpress_connector_url": None,
        "last_successful_connection": None,
        "last_failed_connection": None,
        "last_full_sync": None,
        "last_changed_products_sync": None,
        "connection_health": "not_configured",
    }


@router.get("/deployment-notes")
def deployment_notes() -> dict[str, object]:
    settings = get_settings()
    return {
        "app_host": settings.app_host,
        "app_port": settings.app_port,
        "avoid_ports": [22, 53, 80, 443, 3000, 30303, 8545, 8551, 9000, 3610, 5000, 6363, 9090, 3100, 18550],
        "database_public_exposure": "disabled_by_default",
        "redis_public_exposure": "disabled_by_default",
    }
