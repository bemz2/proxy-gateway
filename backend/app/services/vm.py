from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.virtual_machine import VirtualMachine
from app.schemas.vm import VirtualMachineCreate


def list_virtual_machines(db: Session) -> list[VirtualMachine]:
    return list(db.scalars(select(VirtualMachine).order_by(VirtualMachine.id.asc())).all())


def get_virtual_machine(db: Session, vm_id: int) -> VirtualMachine:
    vm = db.scalar(select(VirtualMachine).where(VirtualMachine.id == vm_id))
    if not vm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Virtual machine not found")
    return vm


def create_virtual_machine(db: Session, payload: VirtualMachineCreate) -> VirtualMachine:
    vm = VirtualMachine(**payload.model_dump())
    db.add(vm)
    try:
        db.commit()
        db.refresh(vm)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="VM with this name already exists")
    return vm
