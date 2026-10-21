from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from app.api.schemas.product import ProductResponse

class ShelfBase(BaseModel):
    name: str = Field("Shelf 01", min_length=1, max_length=255)
    width_cm: float = Field(120.0, gt=0.0, description="Usable shelf width in centimetres")
    total_height_cm: float = Field(180.0, gt=0.0, description="Total shelf height in centimetres")
    depth_cm: float = Field(40.0, gt=0.0, description="Shelf depth in centimetres")
    row_count: int = Field(4, ge=1, le=12, description="Number of shelf rows (1 to 12)")
    has_plinth: bool = Field(False, description="Enable bottom plinth/base header")
    plinth_height_cm: float = Field(0.0, ge=0.0, description="Plinth height in centimetres")
    order_index: int = Field(0, ge=0)

    @field_validator("name")
    @classmethod
    def check_name_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Shelf name cannot be empty.")
        return trimmed

    @model_validator(mode="after")
    def validate_plinth(self):
        if self.has_plinth:
            if self.plinth_height_cm < 0:
                raise ValueError("Plinth height cannot be negative.")
            if self.plinth_height_cm >= self.total_height_cm:
                raise ValueError(
                    f"Plinth height ({self.plinth_height_cm}cm) must be less than total shelf height ({self.total_height_cm}cm)."
                )
        return self

class ShelfCreate(ShelfBase):
    pass

class ShelfUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    width_cm: Optional[float] = Field(None, gt=0.0)
    total_height_cm: Optional[float] = Field(None, gt=0.0)
    depth_cm: Optional[float] = Field(None, gt=0.0)
    row_count: Optional[int] = Field(None, ge=1, le=12)
    has_plinth: Optional[bool] = None
    plinth_height_cm: Optional[float] = Field(None, ge=0.0)
    order_index: Optional[int] = Field(None, ge=0)

    @model_validator(mode="after")
    def validate_plinth(self):
        if self.has_plinth is not None and self.has_plinth:
            if self.plinth_height_cm is not None and self.total_height_cm is not None:
                if self.plinth_height_cm >= self.total_height_cm:
                    raise ValueError("Plinth height must be less than total shelf height.")
        return self

class PlacementInShelf(BaseModel):
    id: int
    shelf_id: int
    product_id: int
    row_index: int
    x_offset_cm: float
    facing_count: int
    product: ProductResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ShelfResponse(ShelfBase):
    id: int
    planogram_id: int
    placements: List[PlacementInShelf] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
