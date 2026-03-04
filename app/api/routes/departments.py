from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentTreeNode,
)
from app.schemas.employee import EmployeeCreate, EmployeeResponse
from app.services.departments import create_department, get_department_tree
from app.services.employees import create_employee

router = APIRouter(prefix="/departments", tags=["departments"])


@router.post("/", response_model=DepartmentResponse, status_code=201)
async def create_department_handler(
    payload: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
) -> DepartmentResponse:
    department = await create_department(db=db, data=payload)
    return DepartmentResponse.model_validate(department)


@router.get("/{department_id}", response_model=DepartmentTreeNode)
async def get_department_handler(
    department_id: int,
    depth: int = Query(1, ge=1, le=5),
    include_employees: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> DepartmentTreeNode:
    return await get_department_tree(
        db=db,
        department_id=department_id,
        depth=depth,
        include_employees=include_employees,
    )


@router.post(
    "/departments/{department_id}/employees",
    response_model=EmployeeResponse,
    status_code=201,
)
async def create_employee_handler(
    department_id: int,
    payload: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
) -> EmployeeResponse:
    employee = await create_employee(
        db=db, department_id=department_id, payload=payload
    )
    return employee
