from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from app.db.models import Product, Planogram, Shelf, Placement, utc_now
from app.services.export_service import export_planogram_json

def test_utc_now_returns_timezone_aware_datetime():
    now = utc_now()
    assert isinstance(now, datetime)
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc

def test_sqlite_foreign_key_enforcement_on_placements(db_session):
    """
    Verifies that SQLite PRAGMA foreign_keys=ON is active and rejects
    inserting child records with nonexistent foreign key references.
    """
    # Create valid planogram and shelf
    plano = Planogram(name="FK Test Planogram")
    db_session.add(plano)
    db_session.commit()

    shelf = Shelf(planogram_id=plano.id, name="FK Shelf", width_cm=100.0, total_height_cm=150.0, depth_cm=40.0)
    db_session.add(shelf)
    db_session.commit()

    # Attempt to insert placement referencing a non-existent product_id
    invalid_placement = Placement(
        shelf_id=shelf.id,
        product_id=99999,  # Non-existent
        row_index=0,
        x_offset_cm=0.0,
        facing_count=1
    )
    db_session.add(invalid_placement)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()
    assert "FOREIGN KEY constraint failed" in str(exc_info.value)
    db_session.rollback()

def test_sqlite_cascade_delete_on_shelf_and_placements(db_session):
    """
    Verifies that deleting a shelf cascades and deletes its placements.
    """
    plano = Planogram(name="Cascade Planogram")
    db_session.add(plano)
    db_session.commit()

    shelf = Shelf(planogram_id=plano.id, name="Cascade Shelf", width_cm=120.0, total_height_cm=180.0, depth_cm=40.0)
    db_session.add(shelf)

    prod = Product(
        sku="CASCADE-SKU-1",
        name="Cascade Product",
        category="Test",
        width_cm=10.0,
        height_cm=15.0,
        depth_cm=5.0,
        price=10.0,
        image_path="uploads/test.png"
    )
    db_session.add(prod)
    db_session.commit()

    placement = Placement(
        shelf_id=shelf.id,
        product_id=prod.id,
        row_index=0,
        x_offset_cm=0.0,
        facing_count=1
    )
    db_session.add(placement)
    db_session.commit()

    assert db_session.query(Placement).filter(Placement.shelf_id == shelf.id).count() == 1

    # Delete shelf
    db_session.delete(shelf)
    db_session.commit()

    # Placement must be gone
    assert db_session.query(Placement).filter(Placement.shelf_id == shelf.id).count() == 0

def test_check_constraints_enforced(db_session):
    """
    Verifies that check constraints (e.g. positive dimensions, non-negative price) are strictly enforced.
    """
    invalid_prod = Product(
        sku="CHECK-NEG-WIDTH",
        name="Invalid Product",
        width_cm=-5.0,  # Invalid
        height_cm=10.0,
        depth_cm=10.0,
        price=10.0,
        image_path="uploads/test.png"
    )
    db_session.add(invalid_prod)
    with pytest.raises(IntegrityError) as exc_info:
        db_session.commit()
    assert "CHECK constraint failed" in str(exc_info.value)
    db_session.rollback()

def test_export_timestamp_format(db_session):
    """
    Verifies export JSON has ISO-8601 UTC timestamp ending in Z.
    """
    plano = Planogram(name="Export Timestamp Plano")
    db_session.add(plano)
    db_session.commit()

    export_data = export_planogram_json(db_session, plano.id)
    assert export_data.exported_at.endswith("Z")
    # Verify parseable
    dt = datetime.fromisoformat(export_data.exported_at.replace("Z", "+00:00"))
    assert dt.tzinfo is not None
