from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "aetherops",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_retry_delay=10,
)
celery_app.autodiscover_tasks(["app.workers"])
