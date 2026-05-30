from app.jobs.celery_app import celery_app


@celery_app.task(name="app.jobs.debug.ping")
def celery_ping() -> str:
    return "pong"
