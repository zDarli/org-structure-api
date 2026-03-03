from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.department import Department
from app.schemas.department import DepartmentCreate


async def create_department(db: AsyncSession, data: DepartmentCreate) -> Department:
    # parent exists
    if data.parent_id is not None:
        res = await db.execute(
            select(Department).where(Department.id == data.parent_id)
        )
        parent = res.scalar_one_or_none()
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent department not found",
            )

    department = Department(name=data.name, parent_id=data.parent_id)
    db.add(department)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department with this name already exists in this parent",
        )

    await db.refresh(department)
    return department


async def get_department_by_id(db: AsyncSession, department_id: int) -> Department:
    res = await db.execute(select(Department).where(Department.id == department_id))
    department = res.scalar_one_or_none()

    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    return department
