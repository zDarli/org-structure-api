from __future__ import annotations

from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.schemas.employee import EmployeeResponse

from enum import Enum


class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or whitespace")
        return v


class DepartmentCreate(DepartmentBase):
    parent_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or whitespace")
        return v


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: Optional[int]


class DepartmentTreeNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    department: DepartmentResponse
    employees: List[EmployeeResponse] = []
    children: List["DepartmentTreeNode"] = []


class DeleteMode(str, Enum):
    cascade = "cascade"
    reassign = "reassign"
