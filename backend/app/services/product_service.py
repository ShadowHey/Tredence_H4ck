import csv
import io
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models import Product, Placement
from app.api.schemas.product import ProductCreate, ProductUpdate

def list_products(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None
) -> Tuple[List[Product], int]:
    query = db.query(Product)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            (Product.name.ilike(search_fmt)) | (Product.sku.ilike(search_fmt))
        )
    if category and category.lower() != "all":
        query = query.filter(Product.category == category)

    total_count = query.count()
    query = query.order_by(Product.name.asc())

    if page is not None and limit is not None:
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
    elif limit is not None:
        query = query.limit(limit)

    return query.all(), total_count

def list_categories(db: Session) -> List[Dict[str, Any]]:
    """
    Returns unique categories with their product count.
    """
    results = (
        db.query(Product.category, func.count(Product.id).label("count"))
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
        .all()
    )
    return [{"category": r[0] or "General", "count": r[1]} for r in results]

def export_products_csv(db: Session) -> str:
    """
    Exports all products to CSV string.
    """
    products = db.query(Product).order_by(Product.sku.asc()).all()
    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "sku", "name", "category", "description", "price",
        "currency", "width_cm", "height_cm", "depth_cm", "image_path", "is_sample"
    ]
    writer.writerow(headers)

    for p in products:
        writer.writerow([
            p.sku,
            p.name,
            p.category or "General",
            p.description or "",
            p.price,
            p.currency,
            p.width_cm,
            p.height_cm,
            p.depth_cm,
            p.image_path,
            p.is_sample,
        ])
    return output.getvalue()

def import_products_csv(db: Session, csv_content: str) -> Dict[str, Any]:
    """
    Imports or updates products from CSV content.
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file is empty or missing headers.")

    required_fields = {"sku", "name", "width_cm", "height_cm", "depth_cm"}
    fieldnames_clean = {f.strip() for f in reader.fieldnames if f}
    missing = required_fields - fieldnames_clean
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"CSV is missing required column(s): {', '.join(sorted(missing))}"
        )

    created_count = 0
    updated_count = 0
    errors = []

    for row_idx, row in enumerate(reader, start=2):
        sku = (row.get("sku") or "").strip()
        name = (row.get("name") or "").strip()
        if not sku or not name:
            errors.append(f"Row {row_idx}: 'sku' and 'name' cannot be empty.")
            continue

        try:
            width_cm = float(row.get("width_cm", 0))
            height_cm = float(row.get("height_cm", 0))
            depth_cm = float(row.get("depth_cm", 0))
            price = float(row.get("price", 0) or 0)
        except ValueError as e:
            errors.append(f"Row {row_idx} ({sku}): Invalid numeric values - {e}")
            continue

        if width_cm <= 0 or height_cm <= 0 or depth_cm <= 0:
            errors.append(f"Row {row_idx} ({sku}): Dimensions (width, height, depth) must be positive floats.")
            continue
        if price < 0:
            errors.append(f"Row {row_idx} ({sku}): Price cannot be negative.")
            continue

        category = (row.get("category") or "General").strip()
        description = (row.get("description") or "").strip() or None
        currency = (row.get("currency") or "INR").strip()
        image_path = (row.get("image_path") or "/placeholder-product.svg").strip()
        is_sample = str(row.get("is_sample", "")).strip().lower() in ("true", "1", "yes")

        existing = get_product_by_sku(db, sku)
        if existing:
            existing.name = name
            existing.category = category
            existing.description = description
            existing.price = price
            existing.currency = currency
            existing.width_cm = width_cm
            existing.height_cm = height_cm
            existing.depth_cm = depth_cm
            if image_path and image_path != "/placeholder-product.svg":
                existing.image_path = image_path
            updated_count += 1
        else:
            product = Product(
                sku=sku,
                name=name,
                category=category,
                description=description,
                price=price,
                currency=currency,
                width_cm=width_cm,
                height_cm=height_cm,
                depth_cm=depth_cm,
                image_path=image_path,
                is_sample=is_sample,
            )
            db.add(product)
            created_count += 1

    if created_count > 0 or updated_count > 0:
        db.commit()

    return {
        "total_rows": created_count + updated_count + len(errors),
        "created": created_count,
        "updated": updated_count,
        "errors": errors,
    }


def get_product_by_id(db: Session, product_id: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found.")
    return product

def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    return db.query(Product).filter(Product.sku == sku.strip()).first()

def create_product(db: Session, product_in: ProductCreate) -> Product:
    # Check unique SKU
    existing = get_product_by_sku(db, product_in.sku)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Product with SKU '{product_in.sku}' already exists (ID: {existing.id}, Name: '{existing.name}')."
        )
        
    product = Product(
        sku=product_in.sku.strip(),
        name=product_in.name.strip(),
        category=product_in.category or "General",
        description=product_in.description,
        price=product_in.price,
        currency=product_in.currency or "INR",
        width_cm=product_in.width_cm,
        height_cm=product_in.height_cm,
        depth_cm=product_in.depth_cm,
        image_path=product_in.image_path,
        is_sample=product_in.is_sample,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def update_product(db: Session, product_id: int, product_in: ProductUpdate) -> Product:
    product = get_product_by_id(db, product_id)
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int) -> dict:
    product = get_product_by_id(db, product_id)
    # Check if used in placements
    usage_count = db.query(Placement).filter(Placement.product_id == product_id).count()
    if usage_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete product '{product.name}' (SKU: {product.sku}) because it is placed {usage_count} time(s) on shelves. Remove its placements from planograms first."
        )
    db.delete(product)
    db.commit()
    return {"message": f"Product '{product.name}' deleted successfully."}
