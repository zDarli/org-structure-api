from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class EmployeeBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)

    @field_validator("full_name", "position")
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Field cannot be empty or whitespace")
        return v


class EmployeeCreate(EmployeeBase):
    hired_at: Optional[date] = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: Optional[date]
    created_at: datetime
