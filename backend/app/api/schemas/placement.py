from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.api.schemas.product import ProductResponse

class PlacementBase(BaseModel):
    product_id: int = Field(..., description="ID of product from catalogue")
    row_index: int = Field(..., ge=0, description="0-indexed shelf row number")
    x_offset_cm: float = Field(0.0, ge=0.0, description="Horizontal start offset in cm from left edge")
    facing_count: int = Field(1, ge=1, description="Number of facings (default 1)")

class PlacementCreate(PlacementBase):
    pass

class PlacementUpdate(BaseModel):
    row_index: Optional[int] = Field(None, ge=0)
    x_offset_cm: Optional[float] = Field(None, ge=0.0)
    facing_count: Optional[int] = Field(None, ge=1)

class PlacementResponse(PlacementBase):
    id: int
    shelf_id: int
    product: ProductResponse
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AutoPackRequest(BaseModel):
    product_id: int = Field(..., description="ID of product to pack")
    row_index: int = Field(..., ge=0, description="Row index to pack into")
    facing_count: int = Field(1, ge=1, description="Number of facings")

class SlotSuggestionResponse(BaseModel):
    shelf_id: int
    product_id: int
    row_index: int
    x_offset_cm: float
    facing_count: int

class AutoArrangeResponse(BaseModel):
    shelf_id: int
    row_index: int
    rearranged_count: int
    placements: list[PlacementResponse]

class BatchPlacementRequest(BaseModel):
    placements: list[PlacementCreate] = Field(..., min_length=1, description="List of placements to create atomically")

