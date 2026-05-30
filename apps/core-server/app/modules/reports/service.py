from io import BytesIO
from openpyxl import Workbook
from reportlab.pdfgen import canvas


class ReportBuilder:
    def build_inventory_excel(self, rows: list[dict]) -> bytes:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Inventory"
        headers = ["Product", "SKU", "Category", "Stock", "Status", "Edit URL"]
        sheet.append(headers)
        for row in rows:
            sheet.append([row.get("name"), row.get("sku"), row.get("category"), row.get("stock_quantity"), row.get("inventory_status"), row.get("product_edit_url")])
        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    def build_inventory_pdf(self, title: str, rows: list[dict]) -> bytes:
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer)
        pdf.drawString(72, 800, title)
        y = 770
        for row in rows[:40]:
            pdf.drawString(72, y, f"{row.get('name')} | {row.get('sku')} | {row.get('stock_quantity')} | {row.get('inventory_status')}")
            y -= 18
        pdf.save()
        return buffer.getvalue()
