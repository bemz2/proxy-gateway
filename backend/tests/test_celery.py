from unittest.mock import MagicMock, patch

import pytest


def test_send_activation_email_console_mode(monkeypatch):
    """Test email sending in console mode"""
    from app.services.email import send_activation_email

    # Capture print output
    printed_output = []

    def mock_print(*args, **kwargs):
        printed_output.append(str(args[0]) if args else "")

    monkeypatch.setattr("builtins.print", mock_print)

    send_activation_email("test@example.com", "abc123def456")

    output = "\n".join(printed_output)
    assert "test@example.com" in output
    assert "abc123def456" in output
    assert "Ключ активации" in output


def test_celery_task_execution(db_session, monkeypatch):
    """Test that Celery task can be called"""
    from app.tasks.email_tasks import send_activation_email_task

    # Mock the actual email sending
    mock_send = MagicMock()
    monkeypatch.setattr("app.services.email.send_activation_email", mock_send)

    # Call the task directly (not via .delay())
    send_activation_email_task("test@example.com", "testkey123")

    mock_send.assert_called_once_with(email_to="test@example.com", activation_key="testkey123")


def test_activation_key_generation():
    """Test that activation keys are properly generated"""
    from app.services.user import _generate_activation_key

    key1 = _generate_activation_key()
    key2 = _generate_activation_key()

    # Keys should be 32 characters (hex)
    assert len(key1) == 32
    assert len(key2) == 32

    # Keys should be unique
    assert key1 != key2

    # Keys should be hex
    assert all(c in "0123456789abcdef" for c in key1)
