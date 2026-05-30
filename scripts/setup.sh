#!/usr/bin/env bash
set -euo pipefail
cp -n .env.example .env || true
docker compose build
docker compose up -d postgres redis
docker compose run --rm core-server alembic upgrade head
