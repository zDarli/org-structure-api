from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate


async def create_employee(
    db: AsyncSession,
    department_id: int,
    payload: EmployeeCreate,
) -> Employee:
    # 1) department exists?
    res = await db.execute(select(Department.id).where(Department.id == department_id))
    if res.scalar_one_or_none() is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Department not found")

    employee = Employee(
        department_id=department_id,
        full_name=payload.full_name,
        position=payload.position,
        hired_at=payload.hired_at,
    )

    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return employee
