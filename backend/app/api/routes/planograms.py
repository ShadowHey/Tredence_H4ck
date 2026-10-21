from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Placement
from app.api.schemas.planogram import (
    PlanogramCreate,
    PlanogramUpdate,
    PlanogramResponse,
    PlanogramSummary,
    PlanogramCloneRequest,
)
from app.api.schemas.shelf import ShelfCreate, ShelfUpdate, ShelfResponse
from app.api.schemas.placement import (
    PlacementCreate,
    PlacementUpdate,
    PlacementResponse,
    AutoPackRequest,
    SlotSuggestionResponse,
    AutoArrangeResponse,
    BatchPlacementRequest,
)
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

@router.post("/planograms/{planogram_id}/clone", response_model=PlanogramResponse, status_code=status.HTTP_201_CREATED)
def clone_planogram(
    planogram_id: int,
    clone_in: Optional[PlanogramCloneRequest] = None,
    db: Session = Depends(get_db)
):
    """Duplicates a planogram along with all shelves and placements as a template."""
    new_name = clone_in.name if clone_in else None
    return planogram_service.clone_planogram(db, planogram_id, new_name=new_name)

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

    target_row = int(placement_in.row_index) if placement_in.row_index is not None else int(placement.row_index)
    target_x = float(placement_in.x_offset_cm) if placement_in.x_offset_cm is not None else float(placement.x_offset_cm)
    target_facings = int(placement_in.facing_count) if placement_in.facing_count is not None else int(placement.facing_count)

    # Validate physical bounds and collision against other placements
    placement_service.validate_placement_bounds_and_overlap(
        shelf=shelf,
        product=product,
        row_index=target_row,
        x_offset_cm=target_x,
        facing_count=target_facings,
        exclude_placement_id=int(placement.id)
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
    
    shelf_id = placement.shelf_id
    row_index = placement.row_index
    deleted_x = placement.x_offset_cm
    deleted_width = (placement.product.width_cm * placement.facing_count) if placement.product else 0.0

    db.delete(placement)
    db.flush()

    # Self-adjustment: shift subsequent products on the same row left to fill the gap
    if deleted_width > 0:
        subsequent = (
            db.query(Placement)
            .filter(
                Placement.shelf_id == shelf_id,
                Placement.row_index == row_index,
                Placement.x_offset_cm > deleted_x,
            )
            .order_by(Placement.x_offset_cm.asc())
            .all()
        )
        for p in subsequent:
            p.x_offset_cm = max(0.0, round(p.x_offset_cm - deleted_width, 1))

    db.commit()
    return {"message": "Placement deleted successfully."}

@router.post("/shelves/{shelf_id}/placements/auto-pack", response_model=PlacementResponse, status_code=status.HTTP_201_CREATED)
def auto_pack_placement(
    shelf_id: int,
    request: AutoPackRequest,
    db: Session = Depends(get_db)
):
    """Finds next available horizontal slot on row and places the product."""
    shelf = shelf_service.get_shelf_by_id(db, shelf_id)
    product = product_service.get_product_by_id(db, request.product_id)
    next_x = placement_service.find_next_available_x(shelf, product, request.row_index, request.facing_count)

    placement = Placement(
        shelf_id=shelf_id,
        product_id=request.product_id,
        row_index=request.row_index,
        x_offset_cm=round(next_x, 2),
        facing_count=request.facing_count,
    )
    db.add(placement)
    db.commit()
    db.refresh(placement)
    return placement

@router.post("/shelves/{shelf_id}/placements/suggest-slot", response_model=SlotSuggestionResponse)
def suggest_slot(
    shelf_id: int,
    request: AutoPackRequest,
    db: Session = Depends(get_db)
):
    """Calculates next open slot coordinate without creating placement."""
    shelf = shelf_service.get_shelf_by_id(db, shelf_id)
    product = product_service.get_product_by_id(db, request.product_id)
    next_x = placement_service.find_next_available_x(shelf, product, request.row_index, request.facing_count)
    return SlotSuggestionResponse(
        shelf_id=shelf_id,
        product_id=request.product_id,
        row_index=request.row_index,
        x_offset_cm=next_x,
        facing_count=request.facing_count
    )

@router.post("/shelves/{shelf_id}/rows/{row_index}/auto-arrange", response_model=AutoArrangeResponse)
def auto_arrange_row(
    shelf_id: int,
    row_index: int,
    db: Session = Depends(get_db)
):
    """Compacts and left-aligns all existing placements on row with 0 gaps."""
    shelf = shelf_service.get_shelf_by_id(db, shelf_id)
    rearranged = placement_service.auto_arrange_row(db, shelf, row_index)
    return AutoArrangeResponse(
        shelf_id=shelf_id,
        row_index=row_index,
        rearranged_count=len(rearranged),
        placements=rearranged
    )

@router.post("/shelves/{shelf_id}/placements/batch", response_model=List[PlacementResponse], status_code=status.HTTP_201_CREATED)
def create_batch_placements(
    shelf_id: int,
    batch_in: BatchPlacementRequest,
    db: Session = Depends(get_db)
):
    """Atomically adds multiple placements to a shelf with cumulative bounds and collision validation."""
    shelf = shelf_service.get_shelf_by_id(db, shelf_id)
    product_ids = {p.product_id for p in batch_in.placements}
    products = db.query(product_service.Product).filter(product_service.Product.id.in_(product_ids)).all()
    lookup = {int(p.id): p for p in products}
    return placement_service.batch_create_placements(db, shelf, batch_in.placements, lookup)


