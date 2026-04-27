from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.virtual_machine import VirtualMachine
from app.schemas.vm import VirtualMachineCreate

logger = get_logger(__name__)


def list_virtual_machines(db: Session, skip: int = 0, limit: int = 100) -> list[VirtualMachine]:
    return list(db.scalars(select(VirtualMachine).offset(skip).limit(limit)))


def get_virtual_machine(db: Session, vm_id: int) -> VirtualMachine:
    vm = db.get(VirtualMachine, vm_id)
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual machine not found")
    return vm


def create_virtual_machine(db: Session, payload: VirtualMachineCreate) -> VirtualMachine:
    vm = VirtualMachine(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        protocol=payload.protocol.value,
        is_active=payload.is_active,
    )
    db.add(vm)
    try:
        db.commit()
        db.refresh(vm)
        logger.info(f"Created new VM: {vm.name} (ID: {vm.id})")
    except IntegrityError:
        db.rollback()
        logger.warning(f"Attempt to create VM with duplicate name: {payload.name}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VM with this name already exists")
    return vm
