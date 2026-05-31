# Architecture

WooCommerce StoreOps separates WordPress collection from Core Server processing. WordPress exposes only necessary WooCommerce data through secure REST endpoints. The Python 3 Core Server owns heavy inventory analysis, scheduled sync, queues, Telegram, reports, dashboard APIs, authentication, RBAC, and logs.

## Modules

- Inventory: active in Phase 1.
- Notifications: Telegram-first skeleton, future multi-channel support.
- Reports: Excel/PDF generation in Core Server.
- Auth/Users/Dashboard: foundation for protected modern admin UX.
- Future: Accounting, Orders, Purchases, Suppliers, Sales Analytics, Financial Reports.


## Localization

Timestamps are stored in UTC Gregorian format and rendered as Jalali or Gregorian only at display/export time.

## Product catalog mirror

Inventory maintains all WooCommerce products and variations by WooCommerce IDs for future accounting, purchases, suppliers, analytics, and financial modules.
