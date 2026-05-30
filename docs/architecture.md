# Architecture

WooCommerce StoreOps separates WordPress collection from Core Server processing. WordPress exposes only necessary WooCommerce data through secure REST endpoints. The Python Core Server owns heavy inventory analysis, scheduled sync, queues, Telegram, reports, dashboard APIs, authentication, RBAC, and logs.

## Modules

- Inventory: active in Phase 1.
- Notifications: Telegram-first skeleton, future multi-channel support.
- Reports: Excel/PDF generation in Core Server.
- Auth/Users/Dashboard: foundation for protected modern admin UX.
- Future: Accounting, Orders, Purchases, Suppliers, Sales Analytics, Financial Reports.
