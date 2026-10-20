from typing import List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models import Planogram, Shelf, Placement, Product
from app.api.schemas.planogram import PlanogramCreate, PlanogramUpdate, PlanogramSummary

def list_planograms(db: Session) -> List[PlanogramSummary]:
    planograms = db.query(Planogram).order_by(Planogram.updated_at.desc()).all()
    summaries = []
    for p in planograms:
        shelf_count = len(p.shelves)
        placement_count = sum(len(s.placements) for s in p.shelves)
        summaries.append(
            PlanogramSummary(
                id=p.id,
                name=p.name,
                description=p.description,
                shelf_count=shelf_count,
                placement_count=placement_count,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return summaries

def get_planogram_by_id(db: Session, planogram_id: int) -> Planogram:
    planogram = db.query(Planogram).filter(Planogram.id == planogram_id).first()
    if not planogram:
        raise HTTPException(status_code=404, detail=f"Planogram with ID {planogram_id} not found.")
    return planogram

def create_planogram(db: Session, planogram_in: PlanogramCreate) -> Planogram:
    planogram = Planogram(
        name=planogram_in.name.strip(),
        description=planogram_in.description,
    )
    db.add(planogram)
    db.commit()
    db.refresh(planogram)
    return planogram

def update_planogram(db: Session, planogram_id: int, planogram_in: PlanogramUpdate) -> Planogram:
    planogram = get_planogram_by_id(db, planogram_id)
    update_data = planogram_in.model_dump(exclude_unset=True)
    if "name" in update_data and update_data["name"] is not None:
        trimmed = update_data["name"].strip()
        if not trimmed:
            raise HTTPException(status_code=422, detail="Planogram name cannot be empty.")
        planogram.name = trimmed
    if "description" in update_data:
        planogram.description = update_data["description"]
    db.commit()
    db.refresh(planogram)
    return planogram

def delete_planogram(db: Session, planogram_id: int) -> dict:
    planogram = get_planogram_by_id(db, planogram_id)
    db.delete(planogram)
    db.commit()
    return {"message": f"Planogram '{planogram.name}' deleted successfully."}

def get_dashboard_metrics(db: Session) -> Dict[str, Any]:
    """
    Computes genuine real metrics from SQLite database.
    Does not fake business metrics.
    """
    total_planograms = db.query(Planogram).count()
    total_products = db.query(Product).count()
    total_shelves = db.query(Shelf).count()
    total_placements = db.query(Placement).count()

    recent_planograms = list_planograms(db)[:5]

    return {
        "total_planograms": total_planograms,
        "total_products": total_products,
        "total_shelves": total_shelves,
        "total_placements": total_placements,
        "recent_planograms": [r.model_dump() for r in recent_planograms],
    }
