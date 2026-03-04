from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.department import Department
from app.schemas.department import DepartmentCreate
from app.models.employee import Employee
from app.schemas.department import DepartmentResponse, DepartmentTreeNode
from app.schemas.employee import EmployeeResponse

from collections import defaultdict
from typing import Dict, List, Set


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


async def get_department_tree(
    db: AsyncSession,
    department_id: int,
    depth: int = 1,
    include_employees: bool = True,
) -> DepartmentTreeNode:
    # 1) root
    res = await db.execute(select(Department).where(Department.id == department_id))
    root = res.scalar_one_or_none()
    if root is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )

    # depth=1 -> только корень
    all_departments: List[Department] = [root]
    current_level: List[int] = [root.id]
    all_ids: Set[int] = {root.id}

    # 2) собрать департаменты по уровням
    for _ in range(depth - 1):
        if not current_level:
            break

        res = await db.execute(
            select(Department)
            .where(Department.parent_id.in_(current_level))
            .order_by(Department.name, Department.id)
        )
        children = list(res.scalars().all())

        if not children:
            break

        all_departments.extend(children)
        current_level = [d.id for d in children]
        all_ids.update(current_level)

    # 3) сотрудники одним запросом
    employees_by_dep: Dict[int, List[EmployeeResponse]] = defaultdict(list)
    if include_employees and all_ids:
        res = await db.execute(
            select(Employee)
            .where(Employee.department_id.in_(all_ids))
            .order_by(Employee.full_name, Employee.id)
        )
        for e in res.scalars().all():
            employees_by_dep[e.department_id].append(EmployeeResponse.model_validate(e))

    # 4) построить дерево
    node_by_id: Dict[int, DepartmentTreeNode] = {}

    for d in all_departments:
        node_by_id[d.id] = DepartmentTreeNode(
            department=DepartmentResponse.model_validate(d),
            employees=employees_by_dep.get(d.id, []) if include_employees else [],
            children=[],
        )

    for d in all_departments:
        if d.parent_id is not None and d.parent_id in node_by_id:
            node_by_id[d.parent_id].children.append(node_by_id[d.id])

    return node_by_id[root.id]
