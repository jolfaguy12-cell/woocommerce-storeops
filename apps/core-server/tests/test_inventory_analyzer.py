from app.modules.inventory.models import InventoryStatus, Product
from app.modules.inventory.service import InventoryAnalyzer


def test_low_stock_classification_without_db_session():
    product = Product(product_id=1, name="Test", stock_quantity=1, stock_status="instock", manage_stock=True)
    analyzer = InventoryAnalyzer(db=None)  # type: ignore[arg-type]
    assert analyzer.classify(product) == InventoryStatus.low_stock


def test_invalid_stock_config_when_not_managed():
    product = Product(product_id=1, name="Test", stock_quantity=None, stock_status="instock", manage_stock=False)
    analyzer = InventoryAnalyzer(db=None)  # type: ignore[arg-type]
    assert analyzer.classify(product) == InventoryStatus.invalid_stock_config
