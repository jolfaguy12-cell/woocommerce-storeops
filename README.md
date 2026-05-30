# WooCommerce StoreOps

WooCommerce StoreOps is a modular store-management platform for WooCommerce stores. It is designed around a lightweight WordPress connector and a Python 3 Core Server that performs heavy processing outside the WordPress request lifecycle.

## 1. Project overview

Phase 1 rebuilds the repository from scratch with a production-oriented foundation. The active module is Inventory; future modules include Accounting, Orders, Purchases, Suppliers, Sales Analytics, Financial Reports, and advanced notifications.

## 2. Architecture explanation

- **WordPress Connector Plugin**: minimal WooCommerce plugin exposing secure product and variation inventory endpoints.
- **Python 3 Core Server**: FastAPI application responsible for inventory analysis, auth, queues, Telegram, reports, logs, and dashboard APIs.
- **Admin Dashboard**: API-first skeleton for a future React/Next.js/Tailwind interface.
- **Notification System**: Core-owned Telegram integration with duplicate-alert prevention planned in worker flows.
- **Report Builder**: Core-owned Excel/PDF generation.
- **Inventory Module**: first active module, supporting low stock, out of stock, old out of stock, back in stock, ignored, snoozed, and invalid stock config states.

The key performance rule is that WordPress must not perform heavy analysis, report generation, Telegram messaging, or normal-traffic full scans. The WordPress Connector is only a secure bridge for WooCommerce data, while all inventory rules, reports, Telegram settings, user management, localization, analytics, and future accounting/purchasing modules belong to the Python 3 Core Server.


## 3. Repository structure

```text
apps/core-server/          Python 3 FastAPI Core Server
apps/wordpress-connector/  Lightweight WordPress/WooCommerce plugin
packages/api-contracts/    Shared API schemas
packages/shared-docs/      Shared business requirements notes
docs/                      Architecture, setup, security, API, reports, inventory docs
deployment/                Nginx, Docker, Supervisor deployment assets
scripts/                   Setup and backup scripts
```

## 4. Technology stack

- Python 3.11 or newer
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Redis
- Celery and Celery Beat
- python-telegram-bot
- openpyxl and ReportLab
- Docker and Nginx
- Future dashboard: React/Next.js/Tailwind

## 5. WordPress Connector installation

1. Copy `apps/wordpress-connector` into `wp-content/plugins/woocommerce-storeops-connector`.
2. Activate it from WordPress Admin.
3. Open **Settings → StoreOps Connector**.
4. Enable the connector, enter the Core Server URL, API key, and HMAC secret.
5. Keep inventory thresholds, Telegram, reports, alerts, and business settings out of WordPress; they are configured only in the Python 3 Core Server dashboard.

## 6. Python 3 Core Server installation

```bash
cd apps/core-server
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 7. Environment variables

Copy `.env.example` to `.env` and replace every placeholder secret. Required variables include database, Redis, WordPress API key, HMAC secret, JWT secret, inventory defaults, Telegram settings, and log settings.

## 8. Database setup

PostgreSQL is the system of record. Before running migrations, confirm that `DATABASE_URL` uses the correct host for how you are running the Core Server:

- Inside Docker Compose, use the Compose service name, usually `postgres`.
- Directly on your server or workstation, use `127.0.0.1` or `localhost`.

Docker Compose example:

```env
DATABASE_URL=postgresql+psycopg://storeops:storeops_password@postgres:5432/storeops
```

Local development example:

```env
DATABASE_URL=postgresql+psycopg://storeops:storeops_password@127.0.0.1:5432/storeops
```

Run the database connectivity check before Alembic migrations:

```bash
python3 scripts/check_db.py
```

Run migrations with:

```bash
cd apps/core-server
source .venv/bin/activate
alembic upgrade head
```

## 9. Redis setup

Redis is used for cache and Celery broker/result backend. Docker Compose starts Redis automatically.

## 10. Celery worker setup

```bash
cd apps/core-server
celery -A app.jobs.celery_app.celery_app worker --loglevel=info
```

## 11. Scheduler setup

```bash
cd apps/core-server
celery -A app.jobs.celery_app.celery_app beat --loglevel=info
```

Default inventory schedules are a fast scan every 60 seconds and a daily full scan target at 03:00 AM.

Verify that workers registered the scheduled tasks:

```bash
docker compose exec celery-worker celery -A app.jobs.celery_app.celery_app inspect registered
docker compose logs celery-worker --tail=100
docker compose logs celery-beat --tail=100
```

If `inspect registered` returns `- empty -`, the worker is running but task modules were not imported into the Celery app. Check `celery_app.conf.imports`, explicit task-module imports, and the Docker Compose `-A app.jobs.celery_app.celery_app` app path.

The registered task list must include `app.jobs.inventory_tasks.fast_inventory_scan` and the debug task `app.jobs.debug_tasks.celery_ping`. You can trigger the debug task from inside the worker container:

```bash
docker compose exec celery-worker celery -A app.jobs.celery_app.celery_app call app.jobs.debug_tasks.celery_ping
```

If the worker previously received unregistered task messages, restart the worker and beat after deploying the fix:

```bash
docker compose up -d --build core-server celery-worker celery-beat
docker compose restart celery-worker celery-beat
```

If old broken messages remain in Redis, purge only when it is safe and no important jobs are pending:

```bash
docker compose exec celery-worker celery -A app.jobs.celery_app.celery_app purge
```

## 12. HTTPS/SSL setup

Production traffic must use HTTPS. Set `ENVIRONMENT=production` and `REJECT_INSECURE_HTTP=true`. Replace the sample Nginx certificate paths with valid certificates from Let's Encrypt or your certificate provider.

## 13. Telegram bot setup

1. Create a Telegram bot with BotFather.
2. Set `TELEGRAM_ENABLED=true`.
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WAREHOUSE_CHAT_ID` in the Core Server environment.
4. Use dashboard or API actions to send test messages.

Supported commands planned for the Core Server are `status`, `low`, `out`, `report`, `summary`, and `help`.

## 14. WooCommerce setup

WooCommerce products should be synced as a complete catalog mirror, whether manage stock is enabled or disabled. The connector supports simple products, variable products, and variations, and exposes WooCommerce product IDs, variation IDs, parent IDs, product type, product status, SKUs, category IDs/names, stock status, quantity, edit URL, creation time, and modification time.

## 15. API security setup

- Use HTTPS in production.
- Use API key authentication.
- Sign Core ingestion requests with HMAC and timestamps.
- Reject replayed requests outside timestamp tolerance.
- Enable rate limiting.
- Log failed authentication without exposing secrets.

## 16. Dashboard login setup

The Phase 1 auth endpoint issues JWT tokens from the skeleton login route. Production bootstrap must seed the first Super Admin user with a securely hashed password.

## 17. Role management guide

Built-in roles are Super Admin, Inventory Manager, Sales Manager, Read-only Viewer, Accountant, Purchase Manager, and Supplier Manager. The model is enum-based for Phase 1 and should evolve to permission records as the dashboard grows.

## 18. Report customization guide

Reports are generated by the Core Server. Template options include title, store name, logo, visible columns, included statuses, SKU, variation attributes, category, edit links, stock history, and grouping rules.

## 19. Excel/PDF generation guide

Excel reports use openpyxl. PDF reports use ReportLab. Telegram inline buttons request report generation from the Core Server; WordPress never generates files.

## 20. Telegram command guide

Warehouse channel commands should return clean summaries and report actions. Inline buttons include **Generate Excel** and **Generate PDF**.

## 21. Logging guide

Logging uses Python 3 logging with rotating files and secret redaction. Log categories include WordPress API calls, sync jobs, queue processing, Telegram messages, callbacks, report generation, auth attempts, failed API requests, scheduler runs, database errors, and unexpected exceptions.

## 22. Troubleshooting

### Database name resolution error

If Alembic shows:

```text
sqlalchemy.exc.OperationalError: (psycopg.OperationalError) [Errno -3] Temporary failure in name resolution
```

Check your `DATABASE_URL`. This usually happens when:

- the PostgreSQL host name in `DATABASE_URL` is wrong;
- the app is running outside Docker but `DATABASE_URL` uses a Docker service name such as `postgres` or `db`;
- the PostgreSQL container is not running;
- the Docker Compose network is not active;
- DNS resolution inside the container failed;
- `.env` values were not loaded correctly.

When running inside Docker Compose, the host should usually be the database service name:

```env
DATABASE_URL=postgresql+psycopg://storeops:storeops_password@postgres:5432/storeops
```

When running directly on the server without Docker, the host should usually be `localhost` or `127.0.0.1`:

```env
DATABASE_URL=postgresql+psycopg://storeops:storeops_password@127.0.0.1:5432/storeops
```

Also verify that PostgreSQL is installed and running, the database exists, the user exists, the password is correct, port `5432` is open locally, `.env` is loaded by the application, and Docker containers are running if using Docker Compose.

Useful Docker commands:

```bash
docker compose ps
docker compose up -d postgres
docker compose logs postgres
```

Useful local PostgreSQL commands:

```bash
sudo systemctl status postgresql
sudo -u postgres psql
psql -h 127.0.0.1 -U storeops -d storeops
```

Useful Alembic commands:

```bash
cd apps/core-server
source .venv/bin/activate
alembic upgrade head
```

Run the guided database check from the repository root:

```bash
python3 scripts/check_db.py
```

### Application troubleshooting

- API returns 401: verify API key, HMAC secret, timestamp, and HTTPS settings.
- No products sync: confirm WooCommerce stock management and connector enabled state.
- Worker jobs stuck: confirm Redis URL and Celery worker status. Run `docker compose exec celery-worker celery -A app.jobs.celery_app.celery_app inspect registered` and confirm `app.jobs.inventory_tasks.fast_inventory_scan` is listed. If old invalid messages remain after a deploy, restart `celery-worker` and `celery-beat`; purge Redis queues only if no important jobs are pending.
- Docker build fails while exporting multiple Core Server/Celery images with `failed to prepare extraction snapshot` or `parent snapshot ... does not exist`: this is usually a Docker BuildKit/cache snapshot problem made worse by building the same context for several services in parallel. StoreOps now builds one shared `woocommerce-storeops-core-server:latest` image from `core-server`; `celery-worker` and `celery-beat` reuse that image instead of exporting duplicate builds. Pull this update and run `docker compose build --no-cache core-server && docker compose up -d core-server celery-worker celery-beat`. If Docker still reports the same snapshot error, clean the host builder cache with `docker builder prune` only after confirming no important builds are running.
- Reports fail: confirm dependencies and writable temporary directories.

### Logs

Core Server logs are written to `apps/core-server/app/logs/storeops.log` by default. The database connectivity check writes to `apps/core-server/app/logs/db-check.log`. Logs rotate automatically and must not include secrets.

## Jalali date support

StoreOps stores timestamps as timezone-aware UTC Gregorian values in PostgreSQL. Display/export layers can render dates as Gregorian or Jalali/Persian based on `DATE_DISPLAY_MODE`. The default in `.env.example` is `DATE_DISPLAY_MODE=jalali` with `TIMEZONE=Asia/Tehran`. Dashboard pages, reports, and Telegram messages should call the Core Server datetime utilities instead of storing Jalali values as primary database timestamps.

## User and role management

The Python 3 Core Server owns dashboard user management. It supports username/password login, secure password hashing, user create/update/deactivate endpoints, modular permissions, and audit logs for login, failed login, user creation, role changes, permission changes, and deactivation. Built-in roles are Super Admin, Inventory Manager, Sales Manager, Read-only Viewer, Accountant, Purchase Manager, and Supplier Manager. Only Super Admin should create/delete other administrators by default.

Core permissions include `inventory.view`, `inventory.manage`, `inventory.export`, `reports.view`, `reports.manage`, `telegram.manage`, `users.view`, `users.create`, `users.update`, `users.delete`, `settings.manage`, `logs.view`, and `modules.manage`.

## Importing all WooCommerce products

The Inventory module maintains a complete product catalog mirror, not only low-stock or out-of-stock products. Full sync imports/updates simple products, variable products, variations, in-stock products, out-of-stock products, draft, published, private, pending, and trashed products when accessible from WooCommerce admin APIs. Every record remains linked to WooCommerce through `woocommerce_product_id`, `woocommerce_variation_id`, and `parent_woocommerce_product_id`, so future accounting, purchasing, supplier, cost, profit, and financial report modules can reuse the same catalog records.

The dashboard includes an All Products page with filters for product type, product status, stock status, inventory status, and manage-stock state, plus search by product name, SKU, WooCommerce product ID, and WooCommerce variation ID.

## WordPress Connector minimal responsibility

The WordPress Connector settings page is intentionally limited to connector enabled, Core Server URL, API key, HMAC secret, connection test, connection status, last successful ping, last failed ping, and last successful sync. It must not contain low-stock thresholds, Telegram settings, social network settings, inventory rules, report customization, alert templates, user/role management, product analytics, or accounting preparation.

## Port conflict prevention

This server may already have SSH, DNS, Nginx, Grafana, geth, Lighthouse, Charon, Prometheus, Loki, MEV Boost, and existing Python/Uvicorn services running. Do not bind WooCommerce StoreOps to occupied ports such as `22`, `53`, `80`, `443`, `3000`, `30303`, `8545`, `8551`, `9000`, `3610`, `5000`, `6363`, `9090`, `3100`, or `18550`.

Check occupied ports before deployment:

```bash
ss -tulpn
```

The safe default is:

```env
APP_HOST=127.0.0.1
APP_PORT=8088
```

Change the internal app port in `.env` if `8088` is occupied, then restart Docker Compose. PostgreSQL and Redis are not publicly exposed by default; Docker Compose uses `expose` instead of host `ports` for those services. Public HTTPS should be handled by the existing host Nginx on ports `80`/`443`, proxying a domain/subdomain to `127.0.0.1:8088`.

## Safe deployment with Nginx reverse proxy

Run the Core Server on an internal localhost port and configure the existing Nginx to proxy HTTPS traffic to it. Do not start another public Nginx listener on `80`/`443` if the server already has Nginx running. Avoid conflicts with validator/geth/grafana/nginx services and existing Docker containers.


## Authentication and first Super Admin

Create the first Super Admin after migrations by setting these variables in `.env`:

```env
STOREOPS_ADMIN_USERNAME=admin
STOREOPS_ADMIN_EMAIL=admin@example.com
STOREOPS_ADMIN_PASSWORD=change-this-admin-password
```

Then run from the repository root or inside the Core Server container:

```bash
python3 scripts/create_admin.py
# or
docker compose exec core-server python3 -m app.cli.create_admin
```

The bootstrap command creates a Super Admin only when no users exist, never prints the password, and marks the account to change password on first login. Dashboard auth uses JWT bearer tokens and an HTTP-only `storeops_access_token` cookie for browser sessions.

Password hashes use PBKDF2-SHA256 with per-password salts in the Core Server, so the first-admin bootstrap does not depend on bcrypt and supports long generated passwords without the bcrypt 72-byte input limit.

Auth endpoints:

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/change-password`

## Roles and permissions

Built-in roles are Super Admin, Inventory Manager, Sales Manager, and Read-only Viewer, with future roles prepared for Accountant, Purchase Manager, and Supplier Manager. Permissions include `dashboard.view`, `sync.view`, `sync.run_full`, `sync.run_changed`, `products.view`, `inventory.view`, `inventory.manage`, `reports.view`, `reports.manage`, `users.view`, `users.create`, `users.update`, `users.delete`, `roles.view`, `roles.manage`, `settings.view`, `settings.manage`, and `logs.view`. Only Super Admin can manage users and roles by default.

## Sync Center and product import

The Sync Center runs product sync in Celery, not inside HTTP requests and not in WordPress. Use these endpoints:

- `GET /api/v1/sync/status`
- `GET /api/v1/sync/jobs`
- `GET /api/v1/sync/jobs/{job_id}`
- `POST /api/v1/sync/full-products`
- `POST /api/v1/sync/changed-products`
- `POST /api/v1/sync/check-wordpress`

`POST /api/v1/sync/full-products` queues `app.jobs.inventory_tasks.full_inventory_scan`, creates a `sync_jobs` record, prevents duplicate full syncs, and stores progress and result counts. Product fetches are paginated with a safe batch size of 50 to avoid WordPress overload.

## All Products API

Use `GET /api/v1/products` with `products.view` permission to inspect synced products. It supports pagination, sorting, and filters for search, product type/status, stock status, manage stock, SKU, WooCommerce product ID, variation ID, and parent product ID.

## Celery sync troubleshooting

```bash
docker compose logs celery-worker --tail=100
docker compose logs celery-beat --tail=100
docker compose exec celery-worker celery -A app.jobs.celery_app.celery_app inspect registered
```

Verify products after sync:

```bash
curl -H "Authorization: Bearer <token>" "http://127.0.0.1:8088/api/v1/products?per_page=20"
curl -H "Authorization: Bearer <token>" "http://127.0.0.1:8088/api/v1/sync/jobs"
```

## 23. Deployment checklist

- Replace all secrets.
- Enable HTTPS.
- Run migrations.
- Start Core Server, Celery worker, Celery Beat, PostgreSQL, Redis, and Nginx.
- Configure backups and log rotation.
- Test WordPress connection and Telegram test message.

## 24. Security checklist

- Never store Telegram tokens in WordPress.
- Never commit `.env`.
- Use strong API and HMAC secrets.
- Keep server clocks synchronized.
- Restrict dashboard users by role.
- Review logs for failed authentication attempts.

## 25. Performance recommendations

- Use cursor-based sync.
- Prefer fast changed-product scans after orders and stock changes.
- Run full scans off-peak at 03:00 AM.
- Keep expensive analysis in Celery workers.
- Index inventory product identity and status columns.

## 26. Backup and restore instructions

Run `scripts/backup.sh` to create PostgreSQL dumps. Store backups off-server and test restore regularly.

## 27. Future development notes

Next phases should complete dashboard UI, permission management, production-grade Telegram command handling, report template persistence, full duplicate-alert workflows, and future modules without moving heavy work into WordPress.

## Admin web panel foundation

The Core Server now serves the first browser-based admin panel directly from FastAPI. Open the panel at:

```text
http://127.0.0.1:8088/login
```

After successful login, authenticated users are redirected to `/dashboard`. Protected admin routes such as `/dashboard`, `/sync`, `/products`, `/users`, `/settings`, `/logs`, and `/modules` check the HTTP-only `storeops_access_token` cookie and redirect unauthenticated users back to `/login`.

The admin layout includes a sidebar, top bar, current-user badge, logout button, page titles, cards, tables, loading/empty states, toast notifications, and a confirmation-modal foundation. Future module placeholders are visible as “Coming Soon” items only; no accounting, purchasing, supplier, or financial-report business logic is implemented in this phase.

### Create the first Super Admin

Set the bootstrap variables in `.env`:

```env
STOREOPS_ADMIN_USERNAME=admin
STOREOPS_ADMIN_EMAIL=admin@example.com
STOREOPS_ADMIN_PASSWORD=replace-with-a-long-secure-password
```

Then run either command:

```bash
docker compose exec core-server python3 scripts/create_admin.py
# or
docker compose exec core-server python3 -m app.cli.create_admin
```

The bootstrap command creates the first Super Admin only when no users exist. It refuses to create duplicate initial admins and never prints the password. Passwords are hashed before storage; plain-text passwords are never stored.

### Login and logout

Use the browser login page at `/login`, or call the API directly:

```bash
curl -i -X POST "http://127.0.0.1:8088/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"replace-with-a-long-secure-password"}'
```

The login endpoint accepts username or email and password, logs successful and failed login attempts, applies basic in-memory failed-login lockout protection, returns a bearer token, and sets an HTTP-only browser cookie. Logout is available from the panel and through `POST /api/v1/auth/logout`.

### Users, roles, and permissions

The admin foundation includes database tables for `users`, `roles`, `permissions`, `role_permissions`, and `audit_logs`. Default roles are:

- Super Admin
- Inventory Manager
- Sales Manager
- Read-only Viewer
- Accountant, Purchase Manager, and Supplier Manager as prepared future roles

Permissions are modular and include dashboard, sync, products, inventory, reports, notifications, users, roles, settings, logs, and modules permissions. Only Super Admin users can manage users and roles by default. User-management actions are logged to audit logs.

The **Users & Roles** page is available at `/users`. The API endpoints remain under `/api/v1/users`.

### Database-backed settings

Runtime and business settings now live in the `system_settings` table instead of being hardcoded. Environment variables remain for bootstrap and infrastructure-level values such as database, Redis, JWT secret, and first-admin creation.

Settings are grouped in the admin panel at `/settings`:

- General Settings
- WordPress Connector Settings
- Sync Settings
- Inventory Settings
- Notification Settings
- Report Settings
- Security Settings
- System Settings

The settings API is available at:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" http://127.0.0.1:8088/api/v1/settings/
```

Editable settings can be updated with:

```bash
curl -X PATCH "http://127.0.0.1:8088/api/v1/settings/full_sync_batch_size" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value":50}'
```

Settings changes are validated, persisted, and recorded in audit logs. Secret settings are masked when returned to the UI.

### Sync Center and product sync foundation

The **Sync Center** is available at `/sync`. Users with `sync.view` can view sync status and history. Users with `sync.run_full` can trigger a full product sync, and users with `sync.run_changed` can trigger changed-products sync. Sync execution stays in Celery; HTTP requests only queue jobs.

Useful commands:

```bash
docker compose logs core-server --tail=100
docker compose logs celery-worker --tail=100
docker compose logs celery-beat --tail=100
docker compose exec celery-worker celery -A app.jobs.celery_app.celery_app inspect registered
```

Trigger full sync from API:

```bash
curl -X POST "http://127.0.0.1:8088/api/v1/sync/full-products" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

View sync jobs:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" http://127.0.0.1:8088/api/v1/sync/jobs
```

View imported products:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" "http://127.0.0.1:8088/api/v1/products?per_page=25"
```

### Database design principle

The database is intentionally not overbuilt. This phase keeps only the tables required for authentication, RBAC, settings, audit logs, sync jobs, and the WooCommerce product catalog foundation. Future modules such as Accounting, Orders, Purchases, Suppliers, Sales Analytics, and Financial Reports will add their own tables later through small, sequential Alembic migrations when their implementation actually begins.

This keeps the schema minimal, understandable, and future-compatible without pretending that future modules are already implemented.
