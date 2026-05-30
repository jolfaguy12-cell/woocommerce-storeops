# Development Guide

Use Python 3.11 or newer, FastAPI, SQLAlchemy, Alembic, Redis, and Celery. Keep feature code inside bounded modules. Do not add heavy work to the WordPress connector.


Local setup commands should use `python3`, for example `python3 -m venv .venv` and `python3 -m pip install -r apps/core-server/requirements.txt`.

## Product sync development guardrails

Product sync must run in the Python 3 Core Server via Celery. Do not run catalog analysis, report generation, Telegram alerts, or inventory business logic in WordPress. Keep WooCommerce requests paginated with a safe default batch size of 50.
