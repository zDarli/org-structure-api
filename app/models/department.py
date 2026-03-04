from __future__ import annotations

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.employee import Employee


class Department(Base):
    __tablename__ = "departments"

    __table_args__ = (
        UniqueConstraint("name", "parent_id", name="uq_department_name_parent"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # self relationship
    parent: Mapped[Optional["Department"]] = relationship(
        remote_side=[id],
        back_populates="children",
    )

    children: Mapped[List["Department"]] = relationship(
        back_populates="parent",
        cascade="all, delete",
        passive_deletes=True,
    )

    employees: Mapped[List["Employee"]] = relationship(
        back_populates="department",
        cascade="all, delete",
        passive_deletes=True,
    )
