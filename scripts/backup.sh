#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR=${BACKUP_DIR:-./backups}
mkdir -p "$BACKUP_DIR"
docker compose exec -T postgres pg_dump -U storeops storeops > "$BACKUP_DIR/storeops-$(date +%Y%m%d-%H%M%S).sql"
