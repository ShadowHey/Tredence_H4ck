from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models import Shelf, Planogram
from app.api.schemas.shelf import ShelfCreate, ShelfUpdate

def get_shelf_by_id(db: Session, shelf_id: int) -> Shelf:
    shelf = db.query(Shelf).filter(Shelf.id == shelf_id).first()
    if not shelf:
        raise HTTPException(status_code=404, detail=f"Shelf with ID {shelf_id} not found.")
    return shelf

def create_shelf_for_planogram(db: Session, planogram_id: int, shelf_in: ShelfCreate) -> Shelf:
    planogram = db.query(Planogram).filter(Planogram.id == planogram_id).first()
    if not planogram:
        raise HTTPException(status_code=404, detail=f"Planogram with ID {planogram_id} not found.")
        
    shelf = Shelf(
        planogram_id=planogram_id,
        name=shelf_in.name.strip(),
        width_cm=shelf_in.width_cm,
        total_height_cm=shelf_in.total_height_cm,
        depth_cm=shelf_in.depth_cm,
        row_count=shelf_in.row_count,
        has_plinth=shelf_in.has_plinth,
        plinth_height_cm=shelf_in.plinth_height_cm if shelf_in.has_plinth else 0.0,
        order_index=shelf_in.order_index,
        row_heights=shelf_in.row_heights,
    )
    db.add(shelf)
    db.commit()
    db.refresh(shelf)
    return shelf

def update_shelf(db: Session, shelf_id: int, shelf_in: ShelfUpdate) -> Shelf:
    shelf = get_shelf_by_id(db, shelf_id)
    update_data = shelf_in.model_dump(exclude_unset=True)

    # Safe row reduction check
    if "row_count" in update_data and update_data["row_count"] is not None:
        new_row_count = update_data["row_count"]
        if new_row_count < shelf.row_count:
            # Check if any placements exist in rows >= new_row_count
            affected_placements = [p for p in shelf.placements if p.row_index >= new_row_count]
            if affected_placements:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Cannot reduce row count from {shelf.row_count} to {new_row_count}. "
                        f"There are {len(affected_placements)} product placement(s) in rows that would be removed. "
                        f"Move or delete these placements before reducing rows."
                    )
                )

    # Shelf width reduction check: do existing placements exceed new width?
    if "width_cm" in update_data and update_data["width_cm"] is not None:
        new_width = float(update_data["width_cm"])
        for p in shelf.placements:
            item_end = float(p.x_offset_cm) + (float(p.product.width_cm) * p.facing_count)
            if item_end > new_width + 0.01:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Cannot reduce shelf width to {new_width:.1f}cm because '{p.product.name}' "
                        f"extends to {item_end:.1f}cm on Row {p.row_index + 1}."
                    )
                )

    # Vertical clearance check: do existing placements exceed new row vertical clearance?
    new_total_height = float(update_data.get("total_height_cm", shelf.total_height_cm))
    new_row_count = int(update_data.get("row_count", shelf.row_count))
    new_has_plinth = bool(update_data.get("has_plinth", shelf.has_plinth))
    new_plinth_height = float(update_data.get("plinth_height_cm", shelf.plinth_height_cm if new_has_plinth else 0.0))
    new_usable_height = max(0.0, new_total_height - (new_plinth_height if new_has_plinth else 0.0))
    new_row_clearance = new_usable_height / new_row_count if new_row_count > 0 else 0.0

    for p in shelf.placements:
        if p.product and float(p.product.height_cm) > new_row_clearance + 0.01:
            overflow = round(float(p.product.height_cm) - new_row_clearance, 2)
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Cannot update shelf dimensions because product '{p.product.name}' (SKU: {p.product.sku}) "
                    f"height ({float(p.product.height_cm):.1f}cm) exceeds new row clearance ({new_row_clearance:.1f}cm) "
                    f"by {overflow:.1f}cm on Row {p.row_index + 1}."
                )
            )


    for field, value in update_data.items():
        setattr(shelf, field, value)

    # Keep plinth height consistent with toggle
    if not shelf.has_plinth:
        shelf.plinth_height_cm = 0.0

    db.commit()
    db.refresh(shelf)
    return shelf

def delete_shelf(db: Session, shelf_id: int) -> dict:
    shelf = get_shelf_by_id(db, shelf_id)
    db.delete(shelf)
    db.commit()
    return {"message": f"Shelf '{shelf.name}' deleted successfully."}
