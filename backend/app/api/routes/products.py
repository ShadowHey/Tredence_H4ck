from typing import List, Optional
import math
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.schemas.product import (
    ProductResponse,
    ProductCreate,
    ProductUpdate,
    CategoryCountResponse,
    ProductImportResult,
    PaginatedProductsResponse,
)
from app.services import product_service
from app.storage.file_storage import save_uploaded_image

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=List[ProductResponse])
def get_products(
    response: Response,
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: Optional[int] = Query(None, ge=1, description="Page number (1-indexed)"),
    limit: Optional[int] = Query(None, ge=1, le=500, description="Items per page"),
    db: Session = Depends(get_db)
):
    items, total = product_service.list_products(db, search=search, category=category, page=page, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    if page:
        response.headers["X-Page"] = str(page)
    if limit:
        response.headers["X-Limit"] = str(limit)
    return items


@router.get("/categories", response_model=List[CategoryCountResponse])
def get_categories(db: Session = Depends(get_db)):
    """Returns list of distinct categories and product counts."""
    return product_service.list_categories(db)

@router.get("/paginated", response_model=PaginatedProductsResponse)
def get_products_paginated(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=200, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by product name or SKU"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    items, total = product_service.list_products(db, search=search, category=category, page=page, limit=limit)
    total_pages = math.ceil(total / limit) if limit > 0 else 1
    return PaginatedProductsResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.get("/export/csv")
def export_products_csv(db: Session = Depends(get_db)):
    """Exports full product catalogue as CSV."""
    csv_data = product_service.export_products_csv(db)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products_catalogue.csv"}
    )

@router.post("/import/csv", response_model=ProductImportResult)
async def import_products_csv(
    file: UploadFile = File(..., description="CSV file with product catalogue"),
    db: Session = Depends(get_db)
):
    """Imports or updates products from uploaded CSV file."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .csv file.")
    content = await file.read()
    try:
        decoded = content.decode("utf-8")
    except UnicodeDecodeError:
        decoded = content.decode("latin-1")
    return product_service.import_products_csv(db, decoded)



@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return product_service.get_product_by_id(db, product_id)

@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_with_image(
    sku: str = Form(...),
    name: str = Form(...),
    category: Optional[str] = Form("General"),
    description: Optional[str] = Form(None),
    price: float = Form(0.0),
    currency: str = Form("INR"),
    width_cm: float = Form(...),
    height_cm: float = Form(...),
    depth_cm: float = Form(...),
    is_sample: bool = Form(False),
    image: Optional[UploadFile] = File(None),
    image_path: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Validate image presence
    stored_image_path = None
    if image is not None and image.filename:
        stored_image_path = save_uploaded_image(image, subfolder="products")
    elif image_path:
        stored_image_path = image_path.strip()
    else:
        raise HTTPException(
            status_code=400,
            detail="Product image is required. Provide an uploaded file or an image_path."
        )

    # Basic validations
    if width_cm <= 0 or height_cm <= 0 or depth_cm <= 0:
        raise HTTPException(status_code=422, detail="Product dimensions (width, height, depth) must be greater than zero.")
    if price < 0:
        raise HTTPException(status_code=422, detail="Price cannot be negative.")

    product_in = ProductCreate(
        sku=sku,
        name=name,
        category=category,
        description=description,
        price=price,
        currency=currency,
        width_cm=width_cm,
        height_cm=height_cm,
        depth_cm=depth_cm,
        image_path=stored_image_path,
        is_sample=is_sample,
    )
    return product_service.create_product(db, product_in)

@router.post("/direct", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product_direct(
    product_in: ProductCreate,
    db: Session = Depends(get_db)
):
    """Direct JSON payload creation for testing or automated seeding."""
    return product_service.create_product(db, product_in)

@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    return product_service.update_product(db, product_id, product_update)

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    return product_service.delete_product(db, product_id)
