from fastapi import APIRouter

router = APIRouter()

DASHBOARD_PAGES = [
    "Main Dashboard", "Modules", "Inventory", "Inventory Report", "Low Stock", "Out of Stock",
    "Old Out of Stock", "Product History", "Queue Monitor", "Telegram Settings", "Report Builder",
    "Report Templates", "Users & Roles", "Logs", "System Settings", "Accounting", "Orders", "Purchases",
    "Suppliers", "Sales Analytics", "Financial Reports",
]


@router.get("/navigation")
def navigation() -> list[dict[str, str | bool]]:
    return [{"label": page, "enabled": page not in {"Accounting", "Orders", "Purchases", "Suppliers", "Sales Analytics", "Financial Reports"}} for page in DASHBOARD_PAGES]
