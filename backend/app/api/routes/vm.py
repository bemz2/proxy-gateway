from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.vm import VirtualMachineCreate, VirtualMachineResponse
from app.services.auth import get_current_user
from app.services.vm import create_virtual_machine, get_virtual_machine, list_virtual_machines


router = APIRouter()


@router.get("", response_model=list[VirtualMachineResponse])
def get_virtual_machines(
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> list[VirtualMachineResponse]:
    vms = list_virtual_machines(db=db)
    return [VirtualMachineResponse.model_validate(vm) for vm in vms]


@router.get("/{vm_id}", response_model=VirtualMachineResponse)
def get_vm(
    vm_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> VirtualMachineResponse:
    vm = get_virtual_machine(db=db, vm_id=vm_id)
    return VirtualMachineResponse.model_validate(vm)


@router.post("", response_model=VirtualMachineResponse, status_code=status.HTTP_201_CREATED)
def create_vm(
    payload: VirtualMachineCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
) -> VirtualMachineResponse:
    vm = create_virtual_machine(db=db, payload=payload)
    return VirtualMachineResponse.model_validate(vm)
