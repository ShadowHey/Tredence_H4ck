import json
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Product
from app.core.config import settings

router = APIRouter(tags=["Seeding"])

@router.post("/seed")
def seed_sample_catalogue(db: Session = Depends(get_db)):
    """
    Seeds the product catalogue with the 6 sample products and copies sample packshot images.
    Idempotent: updates or preserves existing sample products.
    """
    root_sample_json = settings.BASE_DIR.parent / "sample_assets" / "catalogue.sample.json"
    handoff_sample_json = settings.BASE_DIR.parent / "shelfsense_antigravity_handoff" / "sample_assets" / "catalogue.sample.json"
    
    json_path = root_sample_json if root_sample_json.exists() else handoff_sample_json
    if not json_path.exists():
        return {"status": "error", "message": f"Sample JSON not found at {json_path}"}
        
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    sample_images_dir = json_path.parent / "images"
    target_uploads_dir = settings.UPLOADS_DIR / "sample_products"
    target_uploads_dir.mkdir(parents=True, exist_ok=True)
    
    seeded_count = 0
    updated_count = 0
    
    for item in data.get("products", []):
        sku = item["sku"]
        existing = db.query(Product).filter(Product.sku == sku).first()
        
        # Copy image file to uploads
        src_img_rel = item.get("image", "")
        img_filename = Path(src_img_rel).name
        src_img_path = sample_images_dir / img_filename
        dest_rel_path = f"uploads/sample_products/{img_filename}"
        dest_abs_path = settings.UPLOADS_DIR / "sample_products" / img_filename
        
        if src_img_path.exists():
            shutil.copyfile(src_img_path, dest_abs_path)
            
        if not existing:
            product = Product(
                sku=sku,
                name=item["name"],
                category=item.get("category", "General"),
                description=item.get("description", "Sample product"),
                price=item.get("price", 0.0),
                currency=item.get("currency", "INR"),
                width_cm=item["width_cm"],
                height_cm=item["height_cm"],
                depth_cm=item["depth_cm"],
                image_path=dest_rel_path,
                is_sample=True,
            )
            db.add(product)
            seeded_count += 1
        else:
            existing.image_path = dest_rel_path
            existing.is_sample = True
            updated_count += 1
            
    db.commit()
    return {
        "status": "success",
        "message": f"Sample catalogue seeded: {seeded_count} added, {updated_count} updated.",
        "seeded_count": seeded_count,
        "updated_count": updated_count,
    }
