# Deployment Guide

Use Docker Compose or a managed container platform. Production deployments must terminate HTTPS at Nginx or a load balancer, set `ENVIRONMENT=production`, reject insecure HTTP, run database migrations, and supervise Core Server plus Celery worker and scheduler processes.
