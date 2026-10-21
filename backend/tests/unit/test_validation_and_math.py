import pytest
from pydantic import ValidationError
from fastapi import HTTPException

from app.api.schemas.product import ProductCreate
from app.api.schemas.shelf import ShelfCreate
from app.db.models import Shelf, Product, Placement
from app.services.placement_service import (
    validate_placement_bounds_and_overlap,
    calculate_row_capacity,
    find_next_available_x,
)

def test_product_schema_validation():
    # Valid product
    p = ProductCreate(
        sku="TEST-SKU-1",
        name="Test Item",
        width_cm=10.0,
        height_cm=15.0,
        depth_cm=5.0,
        price=99.9,
        image_path="uploads/test.png"
    )
    assert p.sku == "TEST-SKU-1"

    # Empty SKU rejected
    with pytest.raises(ValidationError):
        ProductCreate(
            sku="   ",
            name="Test Item",
            width_cm=10.0,
            height_cm=15.0,
            depth_cm=5.0,
            image_path="uploads/test.png"
        )

    # Zero / negative dimensions rejected
    with pytest.raises(ValidationError):
        ProductCreate(
            sku="TEST-SKU-2",
            name="Zero Width",
            width_cm=0.0,
            height_cm=15.0,
            depth_cm=5.0,
            image_path="uploads/test.png"
        )

    with pytest.raises(ValidationError):
        ProductCreate(
            sku="TEST-SKU-3",
            name="Negative Height",
            width_cm=10.0,
            height_cm=-5.0,
            depth_cm=5.0,
            image_path="uploads/test.png"
        )

    # Negative price rejected
    with pytest.raises(ValidationError):
        ProductCreate(
            sku="TEST-SKU-4",
            name="Negative Price",
            width_cm=10.0,
            height_cm=15.0,
            depth_cm=5.0,
            price=-10.0,
            image_path="uploads/test.png"
        )

def test_shelf_schema_validation():
    # Valid shelf
    s = ShelfCreate(
        name="Main Gondola",
        width_cm=120.0,
        total_height_cm=180.0,
        depth_cm=45.0,
        row_count=4,
        has_plinth=True,
        plinth_height_cm=15.0
    )
    assert s.row_count == 4

    # Invalid row count: 0 or > 12 rejected
    with pytest.raises(ValidationError):
        ShelfCreate(name="Bad Shelf", row_count=0)

    with pytest.raises(ValidationError):
        ShelfCreate(name="Bad Shelf", row_count=13)

    # Plinth height >= total height rejected
    with pytest.raises(ValidationError):
        ShelfCreate(
            name="Bad Plinth",
            total_height_cm=100.0,
            has_plinth=True,
            plinth_height_cm=100.0
        )

def test_placement_fit_and_collision_math():
    shelf = Shelf(
        id=1,
        planogram_id=1,
        name="Shelf 01",
        width_cm=100.0,
        total_height_cm=150.0,
        depth_cm=40.0,
        row_count=3,
        plinth_height_cm=0.0
    )
    prod_a = Product(id=1, sku="A", name="Prod A", width_cm=20.0, height_cm=10.0, depth_cm=5.0, price=10.0, image_path="")
    prod_b = Product(id=2, sku="B", name="Prod B", width_cm=30.0, height_cm=10.0, depth_cm=5.0, price=10.0, image_path="")

    # Item A placed at 0..20cm on Row 0
    p1 = Placement(id=1, shelf_id=1, product_id=1, row_index=0, x_offset_cm=0.0, facing_count=1)
    p1.product = prod_a
    shelf.placements = [p1]

    # Valid placement: Prod B at 20cm (ends at 50cm <= 100cm)
    validate_placement_bounds_and_overlap(shelf, prod_b, row_index=0, x_offset_cm=20.0, facing_count=1)

    # Overlap placement: Prod B at 10cm (overlaps Prod A at 0..20cm) -> rejected with 422
    with pytest.raises(HTTPException) as exc_info:
        validate_placement_bounds_and_overlap(shelf, prod_b, row_index=0, x_offset_cm=10.0, facing_count=1)
    assert exc_info.value.status_code == 422
    assert "overlaps with existing product" in exc_info.value.detail

    # Out-of-bounds placement: Prod B at 80cm (80 + 30 = 110 > 100) -> rejected with 422
    with pytest.raises(HTTPException) as exc_info2:
        validate_placement_bounds_and_overlap(shelf, prod_b, row_index=0, x_offset_cm=80.0, facing_count=1)
    assert exc_info2.value.status_code == 422
    assert "exceeds shelf width" in exc_info2.value.detail

    # Invalid row index -> rejected with 422
    with pytest.raises(HTTPException) as exc_info3:
        validate_placement_bounds_and_overlap(shelf, prod_b, row_index=5, x_offset_cm=0.0, facing_count=1)
    assert exc_info3.value.status_code == 422
    assert "Invalid row index" in exc_info3.value.detail

def test_row_capacity_calculation():
    shelf = Shelf(id=1, name="Shelf", width_cm=120.0, row_count=2)
    prod = Product(id=1, sku="P1", name="Prod", width_cm=30.0, height_cm=10.0, depth_cm=5.0, price=5.0, image_path="")
    p1 = Placement(id=1, shelf_id=1, product_id=1, row_index=0, x_offset_cm=0.0, facing_count=2) # 60cm
    p1.product = prod
    shelf.placements = [p1]

    cap = calculate_row_capacity(shelf, row_index=0)
    assert cap["total_width_cm"] == 120.0
    assert cap["used_width_cm"] == 60.0
    assert cap["remaining_width_cm"] == 60.0
    assert cap["percent_used"] == 50.0

def test_next_available_x():
    shelf = Shelf(id=1, width_cm=100.0, row_count=1)
    prod = Product(id=1, sku="P1", name="Prod", width_cm=20.0, height_cm=10.0, depth_cm=5.0, price=5.0, image_path="")
    p1 = Placement(id=1, shelf_id=1, product_id=1, row_index=0, x_offset_cm=0.0, facing_count=1)
    p1.product = prod
    shelf.placements = [p1]

    # Next open slot is at 20cm
    next_x = find_next_available_x(shelf, prod, row_index=0)
    assert next_x == 20.0

def test_vertical_clearance_validation():
    # Shelf with total height 100cm, 4 rows -> clearance = 25cm per row
    shelf = Shelf(id=1, width_cm=100.0, total_height_cm=100.0, row_count=4, plinth_height_cm=0.0)
    shelf.placements = []

    # Fits: product height 20cm <= 25cm clearance
    fitting_prod = Product(id=1, sku="FIT", name="Fitting Box", width_cm=10.0, height_cm=20.0, depth_cm=10.0, price=5.0, image_path="")
    validate_placement_bounds_and_overlap(shelf, fitting_prod, row_index=0, x_offset_cm=0.0)

    # Exceeds: product height 30cm > 25cm clearance -> 422
    tall_prod = Product(id=2, sku="TALL", name="Tall Bottle", width_cm=10.0, height_cm=30.0, depth_cm=10.0, price=5.0, image_path="")
    with pytest.raises(HTTPException) as exc_info:
        validate_placement_bounds_and_overlap(shelf, tall_prod, row_index=0, x_offset_cm=0.0)
    assert exc_info.value.status_code == 422
    assert "exceeds row vertical clearance" in exc_info.value.detail

