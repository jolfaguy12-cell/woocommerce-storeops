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

The key performance rule is that WordPress must not perform heavy analysis, report generation, Telegram messaging, or normal-traffic full scans.

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
4. Enable the connector, enter the Core Server URL, and set an API key.
5. Keep Telegram tokens out of WordPress; Telegram is configured only in the Core Server.

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
celery -A app.jobs.celery_app worker -l info
```

## 11. Scheduler setup

```bash
cd apps/core-server
celery -A app.jobs.celery_app beat -l info
```

Default inventory schedules are a fast scan every 60 seconds and a daily full scan target at 03:00 AM.

## 12. HTTPS/SSL setup

Production traffic must use HTTPS. Set `ENVIRONMENT=production` and `REJECT_INSECURE_HTTP=true`. Replace the sample Nginx certificate paths with valid certificates from Let's Encrypt or your certificate provider.

## 13. Telegram bot setup

1. Create a Telegram bot with BotFather.
2. Set `TELEGRAM_ENABLED=true`.
3. Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_WAREHOUSE_CHAT_ID` in the Core Server environment.
4. Use dashboard or API actions to send test messages.

Supported commands planned for the Core Server are `status`, `low`, `out`, `report`, `summary`, and `help`.

## 14. WooCommerce setup

WooCommerce must manage stock for products that should be analyzed. The connector supports simple and variable products and exposes product IDs, variation IDs, SKUs, category, stock status, quantity, edit URL, and modification time.

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
- Worker jobs stuck: confirm Redis URL and Celery worker status.
- Reports fail: confirm dependencies and writable temporary directories.

### Logs

Core Server logs are written to `apps/core-server/app/logs/storeops.log` by default. The database connectivity check writes to `apps/core-server/app/logs/db-check.log`. Logs rotate automatically and must not include secrets.

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
