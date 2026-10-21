from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.db.models import Product, Placement
from app.api.schemas.product import ProductCreate, ProductUpdate

def list_products(
    db: Session,
    search: Optional[str] = None,
    category: Optional[str] = None
) -> List[Product]:
    query = db.query(Product)
    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            (Product.name.ilike(search_fmt)) | (Product.sku.ilike(search_fmt))
        )
    if category and category.lower() != "all":
        query = query.filter(Product.category == category)
    return query.order_by(Product.name.asc()).all()

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

    # Compute and persist vector embedding for the product
    try:
        from app.services.embedding_service import embedding_service
        vec = embedding_service.compute_image_embedding(product.image_path)
        product.embedding = vec
        db.commit()
        db.refresh(product)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Embedding generation deferred/skipped for product {product.id}: {e}")

    return product

def update_product(db: Session, product_id: int, product_in: ProductUpdate) -> Product:
    product = get_product_by_id(db, product_id)
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)

    if "image_path" in update_data:
        try:
            from app.services.embedding_service import embedding_service
            vec = embedding_service.compute_image_embedding(product.image_path)
            product.embedding = vec
            db.commit()
            db.refresh(product)
        except Exception:
            pass

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
