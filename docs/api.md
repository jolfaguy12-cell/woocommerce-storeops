# API Documentation

## Core endpoints

- `GET /health`: service health.
- `POST /api/v1/auth/login`: dashboard authentication with JWT/cookie response.
- `GET /api/v1/inventory/products`: inventory products.
- `GET /api/v1/inventory/summary`: counts by inventory status.
- `POST /api/v1/wordpress/products/changed`: signed ingestion endpoint for changed WordPress products.

## WordPress connector endpoints

- `GET /wp-json/storeops/v1/connection-test`
- `GET /wp-json/storeops/v1/products/changed?cursor=0&limit=100`

## Auth endpoints

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/change-password`

## Sync endpoints

- `GET /api/v1/sync/status`
- `GET /api/v1/sync/jobs`
- `GET /api/v1/sync/jobs/{job_id}`
- `POST /api/v1/sync/full-products`
- `POST /api/v1/sync/changed-products`
- `POST /api/v1/sync/check-wordpress`

## Products endpoint

- `GET /api/v1/products` supports search, pagination, sorting, WooCommerce IDs, SKU, product type/status, stock status, and manage-stock filters.
