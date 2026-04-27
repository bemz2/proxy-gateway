from datetime import datetime, timezone

from sqlalchemy import select

from app.core.celery_app import celery_app
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.user import User
from app.models.virtual_machine import VirtualMachine

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.cleanup_expired_keys")
def cleanup_expired_keys() -> dict[str, int]:
    """Remove expired activation keys from database"""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        expired_users = db.scalars(
            select(User).where(
                User.activation_key.isnot(None),
                User.activation_key_expires.isnot(None),
                User.activation_key_expires < now,
            )
        ).all()

        count = 0
        for user in expired_users:
            logger.info(f"Cleaning expired activation key for user {user.id} ({user.email})")
            user.activation_key = None
            user.activation_key_expires = None
            count += 1

        db.commit()
        logger.info(f"Cleaned up {count} expired activation keys")
        return {"cleaned": count}
    except Exception as e:
        logger.error(f"Error cleaning expired keys: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.cleanup_stale_vm_allocations")
def cleanup_stale_vm_allocations(timeout_hours: int | None = None) -> dict[str, int]:
    """Release VMs that have been allocated for too long without activity"""
    from app.core.config import settings
    
    db = SessionLocal()
    try:
        from datetime import timedelta

        if timeout_hours is None:
            timeout_hours = settings.vm_allocation_timeout_hours
        
        now = datetime.now(timezone.utc)
        stale_threshold = now - timedelta(hours=timeout_hours)

        stale_vms = db.scalars(
            select(VirtualMachine).where(
                VirtualMachine.current_user_id.isnot(None),
                VirtualMachine.last_used_at < stale_threshold,
            )
        ).all()

        count = 0
        for vm in stale_vms:
            logger.info(
                f"Releasing stale VM {vm.id} ({vm.name}) from user {vm.current_user_id}. "
                f"Last used: {vm.last_used_at}"
            )
            vm.current_user_id = None
            count += 1

        db.commit()
        logger.info(f"Released {count} stale VM allocations")
        return {"released": count}
    except Exception as e:
        logger.error(f"Error cleaning stale VM allocations: {e}")
        db.rollback()
        raise
    finally:
        db.close()
