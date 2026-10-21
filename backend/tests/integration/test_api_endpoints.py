import io

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database"] == "healthy"
    assert data["uploads_accessible"] is True

def test_product_crud_and_duplicate_sku(client):
    # Create product with multipart image
    image_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"image": ("test_can.png", io.BytesIO(image_bytes), "image/png")}
    data = {
        "sku": "TEST-INT-001",
        "name": "Integration Cola Can",
        "category": "Beverages",
        "width_cm": 6.5,
        "height_cm": 12.0,
        "depth_cm": 6.5,
        "price": 40.0,
        "currency": "INR",
    }
    res = client.post("/api/v1/products", data=data, files=files)
    assert res.status_code == 201
    prod = res.json()
    assert prod["sku"] == "TEST-INT-001"
    assert "uploads/products/" in prod["image_path"]

    # Duplicate SKU returns 409
    res_dup = client.post("/api/v1/products", data=data, files=files)
    assert res_dup.status_code == 409
    assert "already exists" in res_dup.json()["detail"]

    # GET product by ID
    res_get = client.get(f"/api/v1/products/{prod['id']}")
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Integration Cola Can"

def test_planogram_shelf_and_placement_workflow(client):
    # 1. Create Product
    prod_res = client.post("/api/v1/products/direct", json={
        "sku": "PROD-FLOW-1",
        "name": "Flow Cookie Box",
        "category": "Snacks",
        "width_cm": 15.0,
        "height_cm": 20.0,
        "depth_cm": 5.0,
        "price": 50.0,
        "currency": "INR",
        "image_path": "uploads/sample.png"
    })
    assert prod_res.status_code == 201
    product_id = prod_res.json()["id"]

    # 2. Create Planogram
    plano_res = client.post("/api/v1/planograms", json={
        "name": "Store #42 Snack Bay",
        "description": "Aisle 3 Reference Layout"
    })
    assert plano_res.status_code == 201
    plano_id = plano_res.json()["id"]

    # 3. Add Shelf (width 100cm, 3 rows)
    shelf_res = client.post(f"/api/v1/planograms/{plano_id}/shelves", json={
        "name": "Snack Rack A",
        "width_cm": 100.0,
        "total_height_cm": 180.0,
        "depth_cm": 45.0,
        "row_count": 3,
        "has_plinth": True,
        "plinth_height_cm": 10.0
    })
    assert shelf_res.status_code == 201
    shelf_id = shelf_res.json()["id"]

    # 4. Add Placement on Row 0 at 0cm (width 15cm)
    place_res = client.post(f"/api/v1/shelves/{shelf_id}/placements", json={
        "product_id": product_id,
        "row_index": 0,
        "x_offset_cm": 0.0,
        "facing_count": 1
    })
    assert place_res.status_code == 201
    place_id = place_res.json()["id"]
    assert place_id > 0

    # 5. Overlapping placement on Row 0 at 10cm is rejected with 422
    dup_res = client.post(f"/api/v1/shelves/{shelf_id}/placements", json={
        "product_id": product_id,
        "row_index": 0,
        "x_offset_cm": 10.0,
        "facing_count": 1
    })
    assert dup_res.status_code == 422
    assert "overlaps with existing product" in dup_res.json()["detail"]

    # 6. Out-of-bounds placement on Row 0 at 90cm (90 + 15 = 105 > 100) is rejected with 422
    oob_res = client.post(f"/api/v1/shelves/{shelf_id}/placements", json={
        "product_id": product_id,
        "row_index": 0,
        "x_offset_cm": 90.0,
        "facing_count": 1
    })
    assert oob_res.status_code == 422
    assert "exceeds shelf width" in oob_res.json()["detail"]

    # 7. Check row capacity
    cap_res = client.get(f"/api/v1/shelves/{shelf_id}/capacity/0")
    assert cap_res.status_code == 200
    cap = cap_res.json()
    assert cap["total_width_cm"] == 100.0
    assert cap["used_width_cm"] == 15.0
    assert cap["remaining_width_cm"] == 85.0
    assert cap["percent_used"] == 15.0

    # 8. Check safe row reduction: moving shelf from 3 rows to 0-index row (row_count 1) should pass,
    # but if placement was on row 2, reducing to 2 rows would be rejected.
    # Add placement on Row 2
    client.post(f"/api/v1/shelves/{shelf_id}/placements", json={
        "product_id": product_id,
        "row_index": 2,
        "x_offset_cm": 0.0,
        "facing_count": 1
    })
    # Attempting to reduce row_count to 2 (indices 0, 1) should be rejected because Row 2 has a placement!
    reduce_res = client.patch(f"/api/v1/shelves/{shelf_id}", json={"row_count": 2})
    assert reduce_res.status_code == 422
    assert "Cannot reduce row count" in reduce_res.json()["detail"]

    # 9. Verify JSON Export Schema
    export_res = client.get(f"/api/v1/planograms/{plano_id}/export.json")
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert export_data["format_version"] == "1.0"
    assert export_data["unit"] == "cm"
    assert export_data["planogram_name"] == "Store #42 Snack Bay"
    assert len(export_data["shelves"]) == 1
    assert export_data["shelves"][0]["width_cm"] == 100.0
    assert len(export_data["products"]) == 1
    assert export_data["products"][0]["sku"] == "PROD-FLOW-1"

    # 10. Dashboard metrics reflect real counts
    metrics_res = client.get("/api/v1/planograms/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_planograms"] >= 1
    assert metrics["total_shelves"] >= 1
    assert metrics["total_products"] >= 1

def test_foreign_key_and_integrity_error_responses(client):
    # Non-existent shelf
    res = client.post("/api/v1/shelves/99999/placements", json={
        "product_id": 1,
        "row_index": 0,
        "x_offset_cm": 0.0,
        "facing_count": 1
    })
    assert res.status_code == 404
    assert "Shelf with ID 99999 not found" in res.json()["detail"]

    # Non-existent product
    plano_res = client.post("/api/v1/planograms", json={"name": "FK Test Plano"})
    plano_id = plano_res.json()["id"]
    shelf_res = client.post(f"/api/v1/planograms/{plano_id}/shelves", json={
        "name": "FK Shelf",
        "width_cm": 120.0,
        "total_height_cm": 180.0,
        "depth_cm": 40.0,
        "row_count": 4
    })
    shelf_id = shelf_res.json()["id"]

    res_missing_prod = client.post(f"/api/v1/shelves/{shelf_id}/placements", json={
        "product_id": 88888,
        "row_index": 0,
        "x_offset_cm": 0.0,
        "facing_count": 1
    })
    assert res_missing_prod.status_code == 404
    assert "Product with ID 88888 not found" in res_missing_prod.json()["detail"]


def test_delete_middle_placement_self_adjusts_subsequent_products(client):
    # 1. Create product (width 10cm)
    prod_res = client.post("/api/v1/products/direct", json={
        "sku": "PROD-ADJUST-1",
        "name": "Adjust Can",
        "category": "Beverages",
        "width_cm": 10.0,
        "height_cm": 15.0,
        "depth_cm": 5.0,
        "price": 25.0,
        "currency": "INR",
        "image_path": "uploads/sample.png"
    })
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # 2. Create Planogram and Shelf (width 100cm, 3 rows)
    plano_res = client.post("/api/v1/planograms", json={"name": "Self Adjust Test Bay"})
    assert plano_res.status_code == 201
    plano_id = plano_res.json()["id"]

    shelf_res = client.post(f"/api/v1/planograms/{plano_id}/shelves", json={
        "name": "Bay 1",
        "width_cm": 100.0,
        "total_height_cm": 180.0,
        "depth_cm": 40.0,
        "row_count": 3,
        "has_plinth": True,
        "plinth_height_cm": 15.0
    })
    assert shelf_res.status_code == 201
    shelf_id = shelf_res.json()["id"]

    # 3. Add 4 consecutive products on Row 0:
    # P0 at 0cm, P1 at 10cm, P2 at 20cm, P3 at 30cm
    p0 = client.post(f"/api/v1/shelves/{shelf_id}/placements", json={"product_id": prod_id, "row_index": 0, "x_offset_cm": 0.0, "facing_count": 1}).json()
    p1 = client.post(f"/api/v1/shelves/{shelf_id}/placements", json={"product_id": prod_id, "row_index": 0, "x_offset_cm": 10.0, "facing_count": 1}).json()
    p2 = client.post(f"/api/v1/shelves/{shelf_id}/placements", json={"product_id": prod_id, "row_index": 0, "x_offset_cm": 20.0, "facing_count": 1}).json()
    p3 = client.post(f"/api/v1/shelves/{shelf_id}/placements", json={"product_id": prod_id, "row_index": 0, "x_offset_cm": 30.0, "facing_count": 1}).json()

    # 4. Delete the middle product P1 (at 10cm)
    del_res = client.delete(f"/api/v1/placements/{p1['id']}")
    assert del_res.status_code == 200

    # 5. Verify the remaining placements shifted left to close the gap:
    # P0 should remain at 0cm
    # P2 (previously at 20cm) should now be at 10cm (occupying P1's slot!)
    # P3 (previously at 30cm) should now be at 20cm (occupying P2's previous slot!)
    plano_get = client.get(f"/api/v1/planograms/{plano_id}").json()
    shelf_placements = plano_get["shelves"][0]["placements"]
    assert len(shelf_placements) == 3

    positions = {p["id"]: p["x_offset_cm"] for p in shelf_placements}
    assert positions[p0["id"]] == 0.0
    assert positions[p2["id"]] == 10.0
    assert positions[p3["id"]] == 20.0
