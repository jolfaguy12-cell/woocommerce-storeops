# Inventory Module

Default settings: low-stock threshold 2, full daily scan at 03:00 AM, fast changed-product scan every 1 minute, and old out-of-stock hiding after 30 configurable days.

Statuses: normal, low_stock, out_of_stock, old_out_of_stock, back_in_stock, ignored, snoozed, invalid_stock_config.

The module supports simple and variable products, global/category/product thresholds, exclusions, snoozes, duplicate-alert state, and compact grouping of variations under parent products.


## Complete catalog mirror

The module imports all WooCommerce products and variations, including draft/private/published records and products with manage stock enabled or disabled. Inventory settings such as thresholds, exclusions, and snoozes live in the Python 3 Core Server dashboard, not WordPress.
