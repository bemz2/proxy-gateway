from app.core.celery_app import celery_app
from app.services.email import send_activation_email


@celery_app.task(name="app.tasks.send_activation_email")
def send_activation_email_task(email_to: str, activation_key: str) -> None:
    send_activation_email(email_to=email_to, activation_key=activation_key)
