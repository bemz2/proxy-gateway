import smtplib
from email.message import EmailMessage

from app.core.config import settings


def _build_email_text(activation_key: str) -> str:
    return (
        "Здравствуйте!\n\n"
        "Ваш ключ активации для подключения к прокси-сервису:\n"
        f"{activation_key}\n\n"
        "Если вы не запрашивали этот ключ, просто проигнорируйте письмо.\n"
    )


def send_activation_email(email_to: str, activation_key: str) -> None:
    subject = "Ключ активации Proxy Gateway"
    email_text = _build_email_text(activation_key)

    if settings.use_console_email or not settings.smtp_host:
        print(
            f"[EMAIL] To: {email_to}\n"
            f"Subject: {subject}\n\n"
            f"{email_text}"
        )
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_sender
    message["To"] = email_to
    message.set_content(email_text)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
