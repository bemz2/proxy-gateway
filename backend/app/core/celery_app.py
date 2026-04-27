from celery import Celery
from celery.schedules import crontab

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
    imports=("app.tasks.email_tasks", "app.tasks.cleanup_tasks"),
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

celery_app.conf.beat_schedule = {
    "cleanup-expired-keys-every-hour": {
        "task": "app.tasks.cleanup_expired_keys",
        "schedule": crontab(minute=0),  # Every hour at minute 0
    },
    "cleanup-stale-vm-allocations-every-6-hours": {
        "task": "app.tasks.cleanup_stale_vm_allocations",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
    },
}

celery_app.autodiscover_tasks(["app"])
