from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.department import DepartmentCreate, DepartmentResponse
from app.services.departments import create_department

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/", response_model=DepartmentResponse, status_code=201)
async def create_department_handler(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    department = await create_department(db=db, data=payload)
    return DepartmentResponse.model_validate(department)
