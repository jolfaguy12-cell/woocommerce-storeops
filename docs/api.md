# API Documentation

## Core endpoints

- `GET /health`: service health.
- `POST /api/v1/auth/login`: dashboard authentication skeleton.
- `GET /api/v1/inventory/products`: inventory products.
- `GET /api/v1/inventory/summary`: counts by inventory status.
- `POST /api/v1/wordpress/products/changed`: signed ingestion endpoint for changed WordPress products.

## WordPress connector endpoints

- `GET /wp-json/storeops/v1/connection-test`
- `GET /wp-json/storeops/v1/products/changed?cursor=0&limit=100`
