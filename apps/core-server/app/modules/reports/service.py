from datetime import datetime
from io import BytesIO
from openpyxl import Workbook
from reportlab.pdfgen import canvas

from app.core.datetime_utils import format_date_for_report, utc_now


class ReportBuilder:
    def build_inventory_excel(self, rows: list[dict], generated_at: datetime | None = None) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Inventory"
        sheet.append(["Generated at", format_date_for_report(generated_at or utc_now())])
        headers = ["Product", "SKU", "Category", "Stock", "Status", "Last synced", "Edit URL"]
        sheet.append(headers)
        for row in rows:
            last_synced = row.get("last_synced_at")
            if isinstance(last_synced, datetime):
                last_synced = format_date_for_report(last_synced)
            sheet.append([
                row.get("product_name") or row.get("name"),
                row.get("sku"),
                ", ".join(row.get("category_names", [])) if isinstance(row.get("category_names"), list) else row.get("category"),
                row.get("stock_quantity"),
                row.get("inventory_status"),
                last_synced,
                row.get("product_edit_url"),
            ])
        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def build_inventory_pdf(self, title: str, rows: list[dict], generated_at: datetime | None = None) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.drawString(72, 800, title)
        pdf.drawString(72, 782, f"Generated at: {format_date_for_report(generated_at or utc_now())}")
        y = 750
        for row in rows[:40]:
            pdf.drawString(72, y, f"{row.get('product_name') or row.get('name')} | {row.get('sku')} | {row.get('stock_quantity')} | {row.get('inventory_status')}")
            y -= 18
        pdf.save()
        return buffer.getvalue()
