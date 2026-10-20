from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Placement, Shelf
from app.api.schemas.planogram import (
    PlanogramCreate,
    PlanogramUpdate,
    PlanogramResponse,
    PlanogramSummary,
)
from app.api.schemas.shelf import ShelfCreate, ShelfUpdate, ShelfResponse
from app.api.schemas.placement import PlacementCreate, PlacementUpdate, PlacementResponse
from app.api.schemas.export import PlanogramExportJSON
from app.services import (
    planogram_service,
    shelf_service,
    product_service,
    placement_service,
    export_service,
)

router = APIRouter(tags=["Planograms"])

# --- Planograms ---

@router.get("/planograms", response_model=List[PlanogramSummary])
def get_planograms(db: Session = Depends(get_db)):
    return planogram_service.list_planograms(db)

@router.get("/planograms/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    return planogram_service.get_dashboard_metrics(db)

@router.post("/planograms", response_model=PlanogramResponse, status_code=status.HTTP_201_CREATED)
def create_planogram(planogram_in: PlanogramCreate, db: Session = Depends(get_db)):
    return planogram_service.create_planogram(db, planogram_in)

@router.get("/planograms/{planogram_id}", response_model=PlanogramResponse)
def get_planogram(planogram_id: int, db: Session = Depends(get_db)):
    return planogram_service.get_planogram_by_id(db, planogram_id)

@router.patch("/planograms/{planogram_id}", response_model=PlanogramResponse)
def update_planogram(
    planogram_id: int,
    planogram_in: PlanogramUpdate,
    db: Session = Depends(get_db)
):
    return planogram_service.update_planogram(db, planogram_id, planogram_in)

@router.delete("/planograms/{planogram_id}")
def delete_planogram(planogram_id: int, db: Session = Depends(get_db)):
    return planogram_service.delete_planogram(db, planogram_id)

@router.get("/planograms/{planogram_id}/export.json", response_model=PlanogramExportJSON)
def export_planogram(planogram_id: int, db: Session = Depends(get_db)):
    return export_service.export_planogram_json(db, planogram_id)

# --- Shelves ---

@router.post("/planograms/{planogram_id}/shelves", response_model=ShelfResponse, status_code=status.HTTP_201_CREATED)
def create_shelf(
    planogram_id: int,
    shelf_in: ShelfCreate,
    db: Session = Depends(get_db)
):
    return shelf_service.create_shelf_for_planogram(db, planogram_id, shelf_in)

@router.patch("/shelves/{shelf_id}", response_model=ShelfResponse)
def update_shelf(
    shelf_id: int,
    shelf_in: ShelfUpdate,
    db: Session = Depends(get_db)
):
    return shelf_service.update_shelf(db, shelf_id, shelf_in)

@router.delete("/shelves/{shelf_id}")
def delete_shelf(shelf_id: int, db: Session = Depends(get_db)):
    return shelf_service.delete_shelf(db, shelf_id)

@router.get("/shelves/{shelf_id}/capacity/{row_index}")
def get_row_capacity(shelf_id: int, row_index: int, db: Session = Depends(get_db)):
    shelf = shelf_service.get_shelf_by_id(db, shelf_id)
    if row_index < 0 or row_index >= shelf.row_count:
        raise HTTPException(status_code=422, detail=f"Row index {row_index} out of bounds (0 to {shelf.row_count - 1}).")
    return placement_service.calculate_row_capacity(shelf, row_index)

# --- Placements ---

@router.post("/shelves/{shelf_id}/placements", response_model=PlacementResponse, status_code=status.HTTP_201_CREATED)
def create_placement(
    shelf_id: int,
    placement_in: PlacementCreate,
    db: Session = Depends(get_db)
):
    shelf = shelf_service.get_shelf_by_id(db, shelf_id)
    product = product_service.get_product_by_id(db, placement_in.product_id)

    # Validate physical bounds and collision / overlap
    placement_service.validate_placement_bounds_and_overlap(
        shelf=shelf,
        product=product,
        row_index=placement_in.row_index,
        x_offset_cm=placement_in.x_offset_cm,
        facing_count=placement_in.facing_count
    )

    placement = Placement(
        shelf_id=shelf_id,
        product_id=placement_in.product_id,
        row_index=placement_in.row_index,
        x_offset_cm=round(placement_in.x_offset_cm, 2),
        facing_count=placement_in.facing_count,
    )
    db.add(placement)
    db.commit()
    db.refresh(placement)
    return placement

@router.patch("/placements/{placement_id}", response_model=PlacementResponse)
def update_placement(
    placement_id: int,
    placement_in: PlacementUpdate,
    db: Session = Depends(get_db)
):
    placement = db.query(Placement).filter(Placement.id == placement_id).first()
    if not placement:
        raise HTTPException(status_code=404, detail=f"Placement with ID {placement_id} not found.")

    shelf = placement.shelf
    product = placement.product

    target_row = placement_in.row_index if placement_in.row_index is not None else placement.row_index
    target_x = placement_in.x_offset_cm if placement_in.x_offset_cm is not None else placement.x_offset_cm
    target_facings = placement_in.facing_count if placement_in.facing_count is not None else placement.facing_count

    # Validate physical bounds and collision against other placements
    placement_service.validate_placement_bounds_and_overlap(
        shelf=shelf,
        product=product,
        row_index=target_row,
        x_offset_cm=target_x,
        facing_count=target_facings,
        exclude_placement_id=placement.id
    )

    placement.row_index = target_row
    placement.x_offset_cm = round(target_x, 2)
    placement.facing_count = target_facings
    db.commit()
    db.refresh(placement)
    return placement

@router.delete("/placements/{placement_id}")
def delete_placement(placement_id: int, db: Session = Depends(get_db)):
    placement = db.query(Placement).filter(Placement.id == placement_id).first()
    if not placement:
        raise HTTPException(status_code=404, detail=f"Placement with ID {placement_id} not found.")
    db.delete(placement)
    db.commit()
    return {"message": "Placement deleted successfully."}
