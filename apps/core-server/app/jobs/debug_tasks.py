from app.jobs.celery_app import celery_app


@celery_app.task(name="app.jobs.debug_tasks.celery_ping")
def celery_ping() -> str:
    return "pong"
