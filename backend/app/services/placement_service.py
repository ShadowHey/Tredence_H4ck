from typing import List, Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.db.models import Shelf, Product, Placement

EPSILON_CM = 0.01  # tolerance for floating point comparisons in cm

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
    used_width = sum(p.product.width_cm * p.facing_count for p in placements if p.product)
    remaining_width = max(0.0, shelf.width_cm - used_width)
    percent_used = round((used_width / shelf.width_cm) * 100.0, 1) if shelf.width_cm > 0 else 0.0
    
    return {
        "row_index": row_index,
        "total_width_cm": round(shelf.width_cm, 2),
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
    exclude_placement_id: int = None
) -> None:
    """
    Validates:
    1. Valid row index: 0 <= row_index < shelf.row_count
    2. Usable shelf width: x_offset_cm + product_width * facing_count <= shelf.width_cm
    3. Collision / Overlap: No intersection with existing placements on the same row.
    Raises HTTPException(422) with actionable error message if invalid.
    """
    if row_index < 0 or row_index >= shelf.row_count:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid row index {row_index}. Shelf '{shelf.name}' has {shelf.row_count} rows (indices 0 to {shelf.row_count - 1})."
        )
    
    total_placed_width = product.width_cm * facing_count
    item_end = x_offset_cm + total_placed_width

    # Boundary check
    if item_end > shelf.width_cm + EPSILON_CM:
        overflow_cm = round(item_end - shelf.width_cm, 2)
        raise HTTPException(
            status_code=422,
            detail=(
                f"Cannot place '{product.name}' (SKU: {product.sku}) at {x_offset_cm:.1f}cm. "
                f"Its total width ({total_placed_width:.1f}cm) extends to {item_end:.1f}cm, "
                f"which exceeds shelf width of {shelf.width_cm:.1f}cm by {overflow_cm:.1f}cm."
            )
        )

    # Overlap check against all other placements in the same row
    for other in shelf.placements:
        if exclude_placement_id is not None and other.id == exclude_placement_id:
            continue
        if other.row_index != row_index:
            continue
        
        other_start = other.x_offset_cm
        other_end = other.x_offset_cm + (other.product.width_cm * other.facing_count)
        
        # Check interval overlap: [x_offset_cm, item_end] overlaps [other_start, other_end]
        overlap_start = max(x_offset_cm, other_start)
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
    row_placements = sorted(
        [p for p in shelf.placements if p.row_index == row_index],
        key=lambda p: p.x_offset_cm
    )
    
    total_placed_width = product.width_cm * facing_count
    current_x = 0.0
    
    for p in row_placements:
        p_start = p.x_offset_cm
        p_end = p.x_offset_cm + (p.product.width_cm * p.facing_count)
        if current_x + total_placed_width <= p_start + EPSILON_CM:
            # Fits in the gap before p
            return round(current_x, 2)
        current_x = max(current_x, p_end)
        
    if current_x + total_placed_width <= shelf.width_cm + EPSILON_CM:
        return round(current_x, 2)
        
    raise HTTPException(
        status_code=422,
        detail=(
            f"Cannot fit '{product.name}' (width {total_placed_width:.1f}cm) on Row {row_index + 1}. "
            f"Remaining contiguous space from {current_x:.1f}cm to {shelf.width_cm:.1f}cm is insufficient."
        )
    )
