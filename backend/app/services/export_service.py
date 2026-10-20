from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import Planogram
from app.services.planogram_service import get_planogram_by_id
from app.api.schemas.export import (
    PlanogramExportJSON,
    ExportShelf,
    ExportPlacement,
    ExportProductRef,
)

def export_planogram_json(db: Session, planogram_id: int) -> PlanogramExportJSON:
    planogram = get_planogram_by_id(db, planogram_id)
    
    # Collect unique products
    product_map = {}
    exported_shelves = []
    
    for shelf in planogram.shelves:
        exported_placements = []
        for p in shelf.placements:
            if p.product:
                product_map[p.product.id] = p.product
                exported_placements.append(
                    ExportPlacement(
                        id=p.id,
                        shelf_id=shelf.id,
                        product_sku=p.product.sku,
                        product_name=p.product.name,
                        row_index=p.row_index,
                        x_offset_cm=p.x_offset_cm,
                        facing_count=p.facing_count,
                        product_width_cm=p.product.width_cm,
                        product_height_cm=p.product.height_cm,
                        product_depth_cm=p.product.depth_cm,
                    )
                )
        
        exported_shelves.append(
            ExportShelf(
                id=shelf.id,
                name=shelf.name,
                width_cm=shelf.width_cm,
                total_height_cm=shelf.total_height_cm,
                depth_cm=shelf.depth_cm,
                row_count=shelf.row_count,
                has_plinth=shelf.has_plinth,
                plinth_height_cm=shelf.plinth_height_cm,
                row_heights=shelf.row_heights,
                placements=exported_placements,
            )
        )
        
    exported_products = [
        ExportProductRef(
            id=prod.id,
            sku=prod.sku,
            name=prod.name,
            category=prod.category,
            width_cm=prod.width_cm,
            height_cm=prod.height_cm,
            depth_cm=prod.depth_cm,
            price=prod.price,
            currency=prod.currency,
        )
        for prod in product_map.values()
    ]
    
    return PlanogramExportJSON(
        format_version="1.0",
        unit="cm",
        planogram_id=planogram.id,
        planogram_name=planogram.name,
        description=planogram.description,
        shelves=exported_shelves,
        products=exported_products,
        exported_at=datetime.utcnow().isoformat() + "Z",
    )
