from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.department import DepartmentCreate, DepartmentResponse
from app.services.departments import create_department, get_department_by_id

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/", response_model=DepartmentResponse, status_code=201)
async def create_department_handler(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    department = await create_department(db=db, data=payload)
    return DepartmentResponse.model_validate(department)


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department_handler(
    department_id: int,
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    department = await get_department_by_id(db=db, department_id=department_id)
    return DepartmentResponse.model_validate(department)
