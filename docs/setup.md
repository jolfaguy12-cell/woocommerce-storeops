# Installation Guide

1. Copy `.env.example` to `.env` and replace secrets.
2. Run `docker compose build`.
3. Run `docker compose up -d postgres redis`.
4. Run `docker compose run --rm core-server alembic upgrade head`.
5. Run `docker compose up -d`.
6. Install and configure the WordPress connector plugin.
