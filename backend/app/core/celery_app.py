from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "proxy_gateway",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    imports=("app.tasks.email_tasks",),
)

celery_app.autodiscover_tasks(["app"])
