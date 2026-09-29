from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "qoneqt_creator",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=600,
    task_time_limit=700,
    task_max_retries=3,
    task_default_retry_delay=10,
)

import redis
try:
    redis.Redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2).ping()
except Exception:
    print("WARNING: Redis not available! Falling back to eager synchronous tasks.")
    celery_app.conf.update(task_always_eager=True)

