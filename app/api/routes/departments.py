from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentTreeNode,
)
from app.services.departments import create_department, get_department_tree

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
