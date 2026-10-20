from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

class ProductBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=100, description="Unique product SKU")
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    category: Optional[str] = Field("General", max_length=100)
    description: Optional[str] = Field(None)
    price: float = Field(0.0, ge=0.0, description="Price in currency unit")
    currency: str = Field("INR", max_length=10, description="Currency code, e.g. INR")
    width_cm: float = Field(..., gt=0.0, description="Width in centimetres (> 0)")
    height_cm: float = Field(..., gt=0.0, description="Height in centimetres (> 0)")
    depth_cm: float = Field(..., gt=0.0, description="Depth in centimetres (> 0)")

    @field_validator("sku", "name")
    @classmethod
    def check_non_empty(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty or whitespace only.")
        return trimmed

class ProductCreate(ProductBase):
    image_path: str = Field(..., min_length=1, description="Relative path to stored product image")
    is_sample: bool = Field(False)

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0.0)
    currency: Optional[str] = Field(None, max_length=10)
    width_cm: Optional[float] = Field(None, gt=0.0)
    height_cm: Optional[float] = Field(None, gt=0.0)
    depth_cm: Optional[float] = Field(None, gt=0.0)
    image_path: Optional[str] = None

class ProductResponse(ProductBase):
    id: int
    image_path: str
    is_sample: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
