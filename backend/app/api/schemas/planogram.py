from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.api.schemas.shelf import ShelfResponse

class PlanogramBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Planogram name")
    description: Optional[str] = Field(None, description="Optional notes or description")

    @field_validator("name")
    @classmethod
    def check_name_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Planogram name cannot be empty.")
        return trimmed

class PlanogramCreate(PlanogramBase):
    pass

class PlanogramUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class PlanogramSummary(PlanogramBase):
    id: int
    shelf_count: int = 0
    placement_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PlanogramResponse(PlanogramBase):
    id: int
    shelves: List[ShelfResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
