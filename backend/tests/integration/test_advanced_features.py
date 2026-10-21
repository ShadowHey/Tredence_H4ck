import io

def test_vertical_clearance_api(client):
    # Create product with height 35cm
    p_tall = client.post("/api/v1/products/direct", json={
        "sku": "TALL-DRINK-01",
        "name": "Tall Energy Drink",
        "width_cm": 10.0,
        "height_cm": 35.0,
        "depth_cm": 10.0,
        "price": 50.0,
        "image_path": "uploads/tall.png"
    }).json()

    # Create product with height 15cm
    p_short = client.post("/api/v1/products/direct", json={
        "sku": "SHORT-SNACK-01",
        "name": "Short Snack",
        "width_cm": 10.0,
        "height_cm": 15.0,
        "depth_cm": 10.0,
        "price": 20.0,
        "image_path": "uploads/short.png"
    }).json()

    # Create planogram and shelf with total height 100cm, 4 rows (clearance = 25cm per row)
    plano = client.post("/api/v1/planograms", json={"name": "Clearance Test Bay"}).json()
    shelf = client.post(f"/api/v1/planograms/{plano['id']}/shelves", json={
        "name": "Clearance Shelf",
        "width_cm": 100.0,
        "total_height_cm": 100.0,
        "depth_cm": 30.0,
        "row_count": 4,
        "has_plinth": False
    }).json()

    # 1. Tall product (35cm) on row with 25cm clearance should fail with 422
    fail_res = client.post(f"/api/v1/shelves/{shelf['id']}/placements", json={
        "product_id": p_tall["id"],
        "row_index": 0,
        "x_offset_cm": 0.0,
        "facing_count": 1
    })
    assert fail_res.status_code == 422
    assert "exceeds row vertical clearance" in fail_res.json()["detail"]

    # 2. Short product (15cm) should succeed
    succ_res = client.post(f"/api/v1/shelves/{shelf['id']}/placements", json={
        "product_id": p_short["id"],
        "row_index": 0,
        "x_offset_cm": 0.0,
        "facing_count": 1
    })
    assert succ_res.status_code == 201

    # 3. Updating shelf row_count to 8 (clearance drops to 100/8 = 12.5cm) should fail because 15cm > 12.5cm
    shrink_res = client.patch(f"/api/v1/shelves/{shelf['id']}", json={"row_count": 8})
    assert shrink_res.status_code == 422
    assert "exceeds new row clearance" in shrink_res.json()["detail"]

def test_auto_pack_and_slot_suggestion(client):
    plano = client.post("/api/v1/planograms", json={"name": "AutoPack Plano"}).json()
    shelf = client.post(f"/api/v1/planograms/{plano['id']}/shelves", json={
        "name": "Auto Shelf",
        "width_cm": 50.0,
        "total_height_cm": 150.0,
        "row_count": 3
    }).json()

    p1 = client.post("/api/v1/products/direct", json={
        "sku": "AP-001",
        "name": "Pack Item 1",
        "width_cm": 20.0,
        "height_cm": 20.0,
        "depth_cm": 10.0,
        "image_path": "uploads/ap1.png"
    }).json()

    # Suggest slot on empty row should suggest x=0
    sug_res = client.post(f"/api/v1/shelves/{shelf['id']}/placements/suggest-slot", json={
        "product_id": p1["id"],
        "row_index": 0,
        "facing_count": 1
    })
    assert sug_res.status_code == 200
    assert sug_res.json()["x_offset_cm"] == 0.0

    # Auto pack places at x=0
    pack_res1 = client.post(f"/api/v1/shelves/{shelf['id']}/placements/auto-pack", json={
        "product_id": p1["id"],
        "row_index": 0,
        "facing_count": 1
    })
    assert pack_res1.status_code == 201
    assert pack_res1.json()["x_offset_cm"] == 0.0

    # Next auto pack places at x=20
    pack_res2 = client.post(f"/api/v1/shelves/{shelf['id']}/placements/auto-pack", json={
        "product_id": p1["id"],
        "row_index": 0,
        "facing_count": 1
    })
    assert pack_res2.status_code == 201
    assert pack_res2.json()["x_offset_cm"] == 20.0

    # Shelf width is 50. Third item (width 20) needs 20+20+20=60 > 50 -> should fail with 422
    fail_res = client.post(f"/api/v1/shelves/{shelf['id']}/placements/auto-pack", json={
        "product_id": p1["id"],
        "row_index": 0,
        "facing_count": 1
    })
    assert fail_res.status_code == 422
    assert "Remaining contiguous space" in fail_res.json()["detail"]

def test_auto_arrange_row(client):
    plano = client.post("/api/v1/planograms", json={"name": "Arrange Plano"}).json()
    shelf = client.post(f"/api/v1/planograms/{plano['id']}/shelves", json={
        "name": "Arrange Shelf",
        "width_cm": 100.0,
        "total_height_cm": 150.0,
        "row_count": 2
    }).json()

    p = client.post("/api/v1/products/direct", json={
        "sku": "ARR-01",
        "name": "Arrange Prod",
        "width_cm": 15.0,
        "height_cm": 20.0,
        "depth_cm": 10.0,
        "image_path": "uploads/arr.png"
    }).json()

    # Place two items with large gap: one at x=20, one at x=60
    client.post(f"/api/v1/shelves/{shelf['id']}/placements", json={
        "product_id": p["id"],
        "row_index": 0,
        "x_offset_cm": 20.0,
        "facing_count": 1
    })
    client.post(f"/api/v1/shelves/{shelf['id']}/placements", json={
        "product_id": p["id"],
        "row_index": 0,
        "x_offset_cm": 60.0,
        "facing_count": 1
    })

    # Call auto-arrange on row 0
    arr_res = client.post(f"/api/v1/shelves/{shelf['id']}/rows/0/auto-arrange")
    assert arr_res.status_code == 200
    data = arr_res.json()
    assert data["rearranged_count"] == 2
    # First item compacted to 0, second item compacted to 15.0
    placements = data["placements"]
    assert placements[0]["x_offset_cm"] == 0.0
    assert placements[1]["x_offset_cm"] == 15.0

def test_batch_placements(client):
    plano = client.post("/api/v1/planograms", json={"name": "Batch Plano"}).json()
    shelf = client.post(f"/api/v1/planograms/{plano['id']}/shelves", json={
        "name": "Batch Shelf",
        "width_cm": 100.0,
        "total_height_cm": 150.0,
        "row_count": 2
    }).json()

    p1 = client.post("/api/v1/products/direct", json={
        "sku": "BP-01", "name": "B1", "width_cm": 20.0, "height_cm": 20.0, "depth_cm": 5.0, "image_path": "x"
    }).json()
    p2 = client.post("/api/v1/products/direct", json={
        "sku": "BP-02", "name": "B2", "width_cm": 25.0, "height_cm": 20.0, "depth_cm": 5.0, "image_path": "x"
    }).json()

    # Valid batch: p1 at 0..20, p2 at 20..45
    batch_res = client.post(f"/api/v1/shelves/{shelf['id']}/placements/batch", json={
        "placements": [
            {"product_id": p1["id"], "row_index": 0, "x_offset_cm": 0.0, "facing_count": 1},
            {"product_id": p2["id"], "row_index": 0, "x_offset_cm": 20.0, "facing_count": 1},
        ]
    })
    assert batch_res.status_code == 201
    assert len(batch_res.json()) == 2

    # Conflicting batch: overlapping placements inside same batch request
    conflict_res = client.post(f"/api/v1/shelves/{shelf['id']}/placements/batch", json={
        "placements": [
            {"product_id": p1["id"], "row_index": 1, "x_offset_cm": 10.0, "facing_count": 1},
            {"product_id": p2["id"], "row_index": 1, "x_offset_cm": 15.0, "facing_count": 1},
        ]
    })
    assert conflict_res.status_code == 422
    assert "overlaps with" in conflict_res.json()["detail"] or "Batch collision" in conflict_res.json()["detail"]


def test_planogram_cloning(client):
    # Create source planogram
    plano = client.post("/api/v1/planograms", json={"name": "Master Template", "description": "Summer Standard"}).json()
    shelf = client.post(f"/api/v1/planograms/{plano['id']}/shelves", json={
        "name": "Main Display",
        "width_cm": 120.0,
        "total_height_cm": 180.0,
        "row_count": 4
    }).json()
    p = client.post("/api/v1/products/direct", json={
        "sku": "CLONE-P1", "name": "Clone Prod", "width_cm": 10.0, "height_cm": 15.0, "depth_cm": 5.0, "image_path": "x"
    }).json()
    client.post(f"/api/v1/shelves/{shelf['id']}/placements", json={
        "product_id": p["id"],
        "row_index": 0,
        "x_offset_cm": 0.0,
        "facing_count": 2
    })

    # Clone planogram
    clone_res = client.post(f"/api/v1/planograms/{plano['id']}/clone", json={"name": "Regional Store #10"})
    assert clone_res.status_code == 201
    cloned = clone_res.json()
    assert cloned["name"] == "Regional Store #10"
    assert cloned["id"] != plano["id"]
    assert len(cloned["shelves"]) == 1
    assert cloned["shelves"][0]["id"] != shelf["id"]
    assert len(cloned["shelves"][0]["placements"]) == 1
    assert cloned["shelves"][0]["placements"][0]["product"]["sku"] == "CLONE-P1"

def test_categories_and_pagination(client):
    # Add products in different categories
    client.post("/api/v1/products/direct", json={
        "sku": "CAT-BEV-1", "name": "Drink 1", "category": "Beverages", "width_cm": 5.0, "height_cm": 10.0, "depth_cm": 5.0, "image_path": "x"
    })
    client.post("/api/v1/products/direct", json={
        "sku": "CAT-BEV-2", "name": "Drink 2", "category": "Beverages", "width_cm": 5.0, "height_cm": 10.0, "depth_cm": 5.0, "image_path": "x"
    })
    client.post("/api/v1/products/direct", json={
        "sku": "CAT-SNK-1", "name": "Chips 1", "category": "Snacks", "width_cm": 5.0, "height_cm": 10.0, "depth_cm": 5.0, "image_path": "x"
    })

    # Category aggregation
    cat_res = client.get("/api/v1/products/categories")
    assert cat_res.status_code == 200
    categories = {c["category"]: c["count"] for c in cat_res.json()}
    assert categories["Beverages"] >= 2
    assert categories["Snacks"] >= 1

    # Paginated endpoint
    pag_res = client.get("/api/v1/products/paginated?page=1&limit=2")
    assert pag_res.status_code == 200
    pag_data = pag_res.json()
    assert len(pag_data["items"]) == 2
    assert pag_data["total"] >= 3
    assert pag_data["page"] == 1
    assert pag_data["limit"] == 2
    assert pag_data["total_pages"] >= 2

def test_csv_export_and_import(client):
    # Export CSV
    export_res = client.get("/api/v1/products/export/csv")
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers["content-type"]
    csv_text = export_res.text
    assert "sku,name,category" in csv_text

    # Import CSV
    import_csv_data = """sku,name,category,description,price,currency,width_cm,height_cm,depth_cm,image_path,is_sample
CSV-IMP-001,CSV Imported Cookie,Bakery,Fresh cookies,85.0,INR,12.0,18.0,4.0,uploads/sample.png,False
"""
    files = {"file": ("catalogue.csv", io.BytesIO(import_csv_data.encode("utf-8")), "text/csv")}
    imp_res = client.post("/api/v1/products/import/csv", files=files)
    assert imp_res.status_code == 200
    res_data = imp_res.json()
    assert res_data["created"] == 1
    assert len(res_data["errors"]) == 0

    # Verify imported product is queryable
    get_res = client.get("/api/v1/products?search=CSV-IMP-001")
    assert get_res.status_code == 200
    prods = get_res.json()
    assert len(prods) == 1
    assert prods[0]["name"] == "CSV Imported Cookie"
    assert prods[0]["width_cm"] == 12.0
