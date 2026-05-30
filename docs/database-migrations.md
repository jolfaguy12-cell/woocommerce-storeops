# Database Migration Guide

Create migrations from `apps/core-server` with Alembic and review generated SQL before production deploys.

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```
