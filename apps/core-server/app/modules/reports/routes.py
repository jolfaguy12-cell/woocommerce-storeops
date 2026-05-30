from fastapi import APIRouter

router = APIRouter()

DEFAULT_TEMPLATES = [
    "Daily Inventory Summary", "Printable Warehouse Report", "Low Stock Only", "Out of Stock Only",
    "Full Internal Report", "Manager Telegram Report",
]


@router.get("/templates")
def templates() -> list[str]:
    return DEFAULT_TEMPLATES


@router.post("/inventory/{format}")
def generate_inventory_report(format: str) -> dict[str, str]:
    return {"status": "queued", "format": format}
