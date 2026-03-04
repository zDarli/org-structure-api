from __future__ import annotations

from typing import Optional

from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.models.employee import Employee
from app.schemas.department import DepartmentResponse, DepartmentTreeNode, DeleteMode
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


async def _assert_no_cycle(
    db: AsyncSession,
    department_id: int,
    new_parent_id: Optional[int],
) -> None:
    """
    Запрещаем цикл: нельзя назначить parent так, чтобы department оказался в цепочке своих предков.

    Идея:
    идём от new_parent вверх по parent_id, и если встречаем department_id -> цикл.
    """
    if new_parent_id is None:
        return

    current_id: Optional[int] = new_parent_id
    while current_id is not None:
        if current_id == department_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cycle detected in department tree",
            )

        res = await db.execute(
            select(Department.parent_id).where(Department.id == current_id)
        )
        current_id = res.scalar_one_or_none()
        # Если parent_id == None — дошли до корня, цикла нет


async def update_department(
    db: AsyncSession,
    department_id: int,
    payload: DepartmentUpdate,
) -> Department:
    # 1) find department
    department = await db.get(Department, department_id)
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )

    # 2) compute "new" values (если поле не передали — остаётся старое)
    new_name = payload.name if payload.name is not None else department.name

    # Важно: отличать "не передали" от "передали null".
    # В Pydantic v2: payload.parent_id будет None и если передали null, и если не передали.
    # Если тебе нужно строго различать — можно использовать payload.model_fields_set.
    if "parent_id" in payload.model_fields_set:
        new_parent_id = payload.parent_id  # может быть None (сделать корнем)
    else:
        new_parent_id = department.parent_id

    # 3) parent != self
    if new_parent_id == department_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department cannot be its own parent",
        )

    # 4) если parent задан — он должен существовать
    if new_parent_id is not None:
        parent_exists = await db.execute(
            select(Department.id).where(Department.id == new_parent_id)
        )
        if parent_exists.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent department not found",
            )

    # 5) проверка цикла (только если реально меняем parent_id)
    if new_parent_id != department.parent_id:
        await _assert_no_cycle(
            db=db, department_id=department_id, new_parent_id=new_parent_id
        )

    # 6) apply changes
    department.name = new_name
    department.parent_id = new_parent_id

    # 7) commit (ловим уникальность name+parent_id)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department with same name already exists in this parent",
        )

    await db.refresh(department)
    return department


async def delete_department(
    db: AsyncSession,
    department_id: int,
    mode: DeleteMode,
    reassign_to_department_id: int | None,
) -> None:
    # департамент должен существовать
    dept = await db.get(Department, department_id)
    if dept is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )

    if mode == DeleteMode.reassign:
        if reassign_to_department_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reassign_to_department_id is required for mode=reassign",
            )

        if reassign_to_department_id == department_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="reassign_to_department_id cannot be the same as deleted department",
            )

        # reassign target must exist
        res = await db.execute(
            select(Department.id).where(Department.id == reassign_to_department_id)
        )
        if res.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reassign target department not found",
            )

        # защита от циклов: target не должен быть внутри поддерева удаляемого департамента
        await _assert_no_cycle(
            db=db, department_id=department_id, new_parent_id=reassign_to_department_id
        )

        # 1) переносим только прямых сотрудников удаляемого департамента
        await db.execute(
            update(Employee)
            .where(Employee.department_id == department_id)
            .values(department_id=reassign_to_department_id)
        )

        # 2) перепривязываем только прямых детей к reassign департаменту
        await db.execute(
            update(Department)
            .where(Department.parent_id == department_id)
            .values(parent_id=reassign_to_department_id)
        )

        # 3) удаляем сам департамент (без каскада поддерева — оно сохранится)
        await db.execute(delete(Department).where(Department.id == department_id))

        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete department due to related data",
            )

        return

    # mode == cascade
    # Тут именно DB/ORM cascade: удаляем корень, остальное удалит БД по ON DELETE CASCADE
    try:
        await db.delete(dept)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete department due to related data",
        )
