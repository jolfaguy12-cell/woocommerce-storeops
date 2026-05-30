# Deployment Guide

Use Docker Compose or a managed container platform. Production deployments must terminate HTTPS at Nginx or a load balancer, set `ENVIRONMENT=production`, reject insecure HTTP, run database migrations, and supervise Core Server plus Celery worker and scheduler processes.


Use the existing Nginx on ports 80/443 as the public reverse proxy and proxy to the Core Server on `127.0.0.1:8088` or another free internal port. Do not expose PostgreSQL or Redis publicly.


Build the Core Server image once and reuse it for Celery services. The Compose file builds `woocommerce-storeops-core-server:latest` from `core-server`; `celery-worker` and `celery-beat` run the same image with different commands. This avoids parallel duplicate exports of the same Docker context and reduces BuildKit snapshot/cache failures.
