from typing import List, Optional
from pydantic import BaseModel, Field

class ExportProductRef(BaseModel):
    id: int
    sku: str
    name: str
    category: Optional[str] = None
    width_cm: float
    height_cm: float
    depth_cm: float
    price: float
    currency: str

class ExportPlacement(BaseModel):
    id: int
    shelf_id: int
    product_sku: str
    product_name: str
    row_index: int
    x_offset_cm: float
    facing_count: int
    product_width_cm: float
    product_height_cm: float
    product_depth_cm: float

class ExportShelf(BaseModel):
    id: int
    name: str
    width_cm: float
    total_height_cm: float
    depth_cm: float
    row_count: int
    has_plinth: bool
    plinth_height_cm: float
    placements: List[ExportPlacement] = []

class PlanogramExportJSON(BaseModel):
    format_version: str = Field("1.0", description="Schema version")
    unit: str = Field("cm", description="Measurement unit for coordinates and dimensions")
    planogram_id: int
    planogram_name: str
    description: Optional[str] = None
    shelves: List[ExportShelf] = []
    products: List[ExportProductRef] = []
    exported_at: str
