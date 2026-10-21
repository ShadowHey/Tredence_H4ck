from typing import List, Dict, Optional, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.db.models import Shelf, Product, Placement

EPSILON_CM = 0.01  # tolerance for floating point comparisons in cm

def _num(val: Any) -> float:
    """Helper to ensure scalar float from SQLAlchemy Column/scalar attribute."""
    return float(val) if val is not None else 0.0

def calculate_row_capacity(shelf: Shelf, row_index: int) -> dict:
    """
    Computes deterministic capacity for a specific row in cm.
    Returns:
        total_width_cm: shelf usable width
        used_width_cm: sum of widths of all placed products in this row
        remaining_width_cm: available space
        percent_used: percentage rounded to 1 decimal place
        placement_count: number of placements on this row
    """
    placements = [p for p in shelf.placements if p.row_index == row_index]
    used_width = sum(_num(p.product.width_cm) * p.facing_count for p in placements if p.product)
    shelf_width = _num(shelf.width_cm)
    remaining_width = max(0.0, shelf_width - used_width)
    percent_used = round((used_width / shelf_width) * 100.0, 1) if shelf_width > 0 else 0.0
    
    return {
        "row_index": row_index,
        "total_width_cm": round(shelf_width, 2),
        "used_width_cm": round(used_width, 2),
        "remaining_width_cm": round(remaining_width, 2),
        "percent_used": min(100.0, percent_used),
        "placement_count": len(placements)
    }


def validate_placement_bounds_and_overlap(
    shelf: Shelf,
    product: Product,
    row_index: int,
    x_offset_cm: float,
    facing_count: int = 1,
    exclude_placement_id: Optional[int] = None
) -> None:
    """
    Validates:
    1. Valid row index: 0 <= row_index < shelf.row_count
    2. Vertical clearance: product.height_cm <= row vertical clearance
    3. Usable shelf width: x_offset_cm + product_width * facing_count <= shelf.width_cm
    4. Collision / Overlap: No intersection with existing placements on the same row.
    Raises HTTPException(422) with actionable error message if invalid.
    """
    if row_index < 0 or row_index >= shelf.row_count:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid row index {row_index}. Shelf '{shelf.name}' has {shelf.row_count} rows (indices 0 to {shelf.row_count - 1})."
        )
    
    # Vertical clearance (height) check
    total_height = float(shelf.total_height_cm) if shelf.total_height_cm is not None else 180.0
    plinth_height = float(shelf.plinth_height_cm) if (shelf.has_plinth and shelf.plinth_height_cm is not None) else 0.0
    usable_height = max(0.0, total_height - plinth_height)
    row_clearance = usable_height / shelf.row_count if shelf.row_count and shelf.row_count > 0 else 0.0
    prod_height = float(product.height_cm)
    
    if prod_height > row_clearance + EPSILON_CM:
        overflow_height = round(prod_height - row_clearance, 2)
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot place '{product.name}' (SKU: {product.sku}) on Row {row_index + 1}. "
                f"Product height ({prod_height:.1f}cm) exceeds row vertical clearance "
                f"({row_clearance:.1f}cm) by {overflow_height:.1f}cm."
            )
        )

    total_placed_width = float(product.width_cm) * facing_count
    item_end = float(x_offset_cm) + total_placed_width
    shelf_width = float(shelf.width_cm)

    # Boundary check
    if item_end > shelf_width + EPSILON_CM:
        overflow_cm = round(item_end - shelf_width, 2)
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot place '{product.name}' (SKU: {product.sku}) at {x_offset_cm:.1f}cm. "
                f"Its total width ({total_placed_width:.1f}cm) extends to {item_end:.1f}cm, "
                f"which exceeds shelf width of {shelf_width:.1f}cm by {overflow_cm:.1f}cm."
            )
        )

    # Overlap check against all other placements in the same row
    for other in shelf.placements:
        if exclude_placement_id is not None and other.id == exclude_placement_id:
            continue
        if other.row_index != row_index:
            continue
        
        other_start = float(other.x_offset_cm)
        other_end = other_start + (float(other.product.width_cm) * other.facing_count)
        
        # Check interval overlap: [x_offset_cm, item_end] overlaps [other_start, other_end]
        overlap_start = max(float(x_offset_cm), other_start)
        overlap_end = min(item_end, other_end)
        
        if overlap_end - overlap_start > EPSILON_CM:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Placement overlaps with existing product '{other.product.name}' (SKU: {other.product.sku}) "
                    f"positioned at {other_start:.1f}cm - {other_end:.1f}cm on Row {row_index + 1}. "
                    f"Requested slot is {x_offset_cm:.1f}cm - {item_end:.1f}cm."
                )
            )

def find_next_available_x(shelf: Shelf, product: Product, row_index: int, facing_count: int = 1) -> float:
    """
    Helper to suggest or place at the next open slot from left to right on a row.
    Returns next x_offset_cm. If it doesn't fit, raises HTTPException.
    """
    # First check row validity and vertical clearance
    total_height = float(shelf.total_height_cm) if shelf.total_height_cm is not None else 180.0
    plinth_height = float(shelf.plinth_height_cm) if (shelf.has_plinth and shelf.plinth_height_cm is not None) else 0.0
    usable_height = max(0.0, total_height - plinth_height)
    row_clearance = usable_height / shelf.row_count if shelf.row_count and shelf.row_count > 0 else 0.0
    prod_height = float(product.height_cm)

    if prod_height > row_clearance + EPSILON_CM:
        overflow_height = round(prod_height - row_clearance, 2)
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot fit '{product.name}' (SKU: {product.sku}) on Row {row_index + 1}. "
                f"Product height ({prod_height:.1f}cm) exceeds row vertical clearance "
                f"({row_clearance:.1f}cm) by {overflow_height:.1f}cm."
            )
        )

    row_placements = sorted(
        [p for p in shelf.placements if p.row_index == row_index],
        key=lambda p: float(p.x_offset_cm)
    )
    
    total_placed_width = float(product.width_cm) * facing_count
    current_x = 0.0
    
    for p in row_placements:
        p_start = float(p.x_offset_cm)
        p_end = p_start + (float(p.product.width_cm) * p.facing_count)
        if current_x + total_placed_width <= p_start + EPSILON_CM:
            # Fits in the gap before p
            return round(current_x, 2)
        current_x = max(current_x, p_end)
        
    shelf_width = float(shelf.width_cm)
    if current_x + total_placed_width <= shelf_width + EPSILON_CM:
        return round(current_x, 2)
        
    raise HTTPException(
        status_code=422,
        detail=(
            f"Cannot fit '{product.name}' (width {total_placed_width:.1f}cm) on Row {row_index + 1}. "
            f"Remaining contiguous space from {current_x:.1f}cm to {shelf_width:.1f}cm is insufficient."
        )
    )

def auto_arrange_row(db: Session, shelf: Shelf, row_index: int) -> List[Placement]:
    """
    Auto-arranges/compacts all placements on row_index from left to right (x=0) with 0 gaps.
    Preserves their relative order (by x_offset_cm).
    """
    if row_index < 0 or row_index >= shelf.row_count:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid row index {row_index}. Shelf '{shelf.name}' has {shelf.row_count} rows."
        )

    row_placements: List[Placement] = sorted(
        [p for p in shelf.placements if p.row_index == row_index],
        key=lambda p: (float(p.x_offset_cm), int(p.id) if p.id else 0)
    )

    current_x = 0.0
    for p in row_placements:
        p.x_offset_cm = round(current_x, 2)
        current_x += float(p.product.width_cm) * p.facing_count

    shelf_width = float(shelf.width_cm)
    if current_x > shelf_width + EPSILON_CM:
        overflow_cm = round(current_x - shelf_width, 2)
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot arrange Row {row_index + 1}: total width of placed products ({current_x:.1f}cm) "
                f"exceeds shelf usable width ({shelf_width:.1f}cm) by {overflow_cm:.1f}cm."
            )
        )

    db.commit()
    for p in row_placements:
        db.refresh(p)
    return row_placements

def batch_create_placements(
    db: Session,
    shelf: Shelf,
    placements_data: List[Any],
    product_lookup: Dict[int, Product]
) -> List[Placement]:
    """
    Atomically creates multiple placements on a shelf.
    Validates physical bounds, clearance, and collision/overlaps against existing placements
    and newly staged placements in this batch.
    """
    new_placements: List[Placement] = []

    for p_in in placements_data:
        product = product_lookup.get(p_in.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with ID {p_in.product_id} not found.")

        # Validate against existing placements
        validate_placement_bounds_and_overlap(
            shelf=shelf,
            product=product,
            row_index=p_in.row_index,
            x_offset_cm=p_in.x_offset_cm,
            facing_count=p_in.facing_count,
        )

        # Check against already staged placements in this batch
        item_width = float(product.width_cm) * p_in.facing_count
        item_end = float(p_in.x_offset_cm) + item_width
        for staged in new_placements:
            if staged.row_index != p_in.row_index:
                continue
            staged_end = float(staged.x_offset_cm) + (float(staged.product.width_cm) * staged.facing_count)
            overlap_start = max(float(p_in.x_offset_cm), float(staged.x_offset_cm))
            overlap_end = min(item_end, staged_end)
            if overlap_end - overlap_start > EPSILON_CM:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Batch collision: placement for '{product.name}' (SKU: {product.sku}) "
                        f"at {p_in.x_offset_cm:.1f}cm - {item_end:.1f}cm overlaps with earlier batch item "
                        f"'{staged.product.name}' (SKU: {staged.product.sku}) at {staged.x_offset_cm:.1f}cm - {staged_end:.1f}cm."
                    )
                )

        new_placement = Placement(
            shelf_id=shelf.id,
            product_id=p_in.product_id,
            row_index=p_in.row_index,
            x_offset_cm=round(float(p_in.x_offset_cm), 2),
            facing_count=p_in.facing_count,
        )
        new_placement.product = product
        new_placements.append(new_placement)
        shelf.placements.append(new_placement)
        db.add(new_placement)

    db.commit()
    for p in new_placements:
        db.refresh(p)
    return new_placements


