import { test, expect } from "@playwright/test";

test.describe("ShelfSense AI Planogram Designer — Critical User Journey", () => {
  test("complete end-to-end workflow: create, add shelf, place product, save, reload persistence, and export", async ({
    page,
    request,
  }) => {
    // 1. Health check to ensure backend is responsive
    const healthRes = await request.get("http://localhost:8000/health");
    expect(healthRes.ok()).toBeTruthy();
    const health = await healthRes.json();
    expect(health.status).toBe("ok");

    // 2. Open Dashboard
    await page.goto("http://localhost:3000/");
    await expect(page.getByTestId("dashboard-page")).toBeVisible();
    await expect(page.getByText("ShelfSense AI")).toBeVisible();

    // 3. Create or navigate to Planogram Designer
    await page.getByTestId("create-planogram-btn").click();
    await page.fill('input[placeholder*="Beverages Gondola"]', "E2E Automated Planogram");
    await page.getByRole("button", { name: "Start Designing" }).click();

    // 4. Designer page loads
    await page.waitForURL(/\/designer\?id=\d+/);
    await expect(page.getByTestId("designer-page")).toBeVisible();

    // 5. Confirm shelf canvas starts initially empty
    await expect(page.getByTestId("shelf-canvas-empty")).toBeVisible();
    await expect(page.getByText("Shelf Canvas is Empty")).toBeVisible();

    // 6. Add a shelf unit with dimensions and rows
    await page.getByTestId("canvas-add-shelf-btn").click();
    await expect(page.getByText("Add New Shelf Unit")).toBeVisible();
    await page.getByTestId("modal-add-shelf-submit").click();

    // 7. Verify shelf appears on canvas and in Blender outliner
    await expect(page.getByTestId("shelf-canvas")).toBeVisible();
    await expect(page.getByTestId("blender-outliner")).toBeVisible();
    await expect(page.getByText(/Total Usable Width: 120 cm/i)).toBeVisible();
    await expect(page.getByText(/Total 180cm/i)).toBeVisible();

    // 8. Open Product Library tab
    await page.getByTestId("tab-library").click();
    await expect(page.getByTestId("product-library-panel")).toBeVisible();

    // 9. Verify sample products exist (or seed if empty)
    const productCard = page.locator('[data-testid^="catalogue-product-"]').first();
    await expect(productCard).toBeVisible();

    // 10. Add first product to shelf row 1
    const addProductBtn = productCard.getByRole("button", { name: /Add/i });
    if (await addProductBtn.isVisible()) {
      await addProductBtn.click();
    }

    // 11. Verify placement appears on visible row
    const placementElem = page.locator('[data-testid^="placement-"]').first();
    await expect(placementElem).toBeVisible({ timeout: 5000 });

    // 12. Save planogram explicitly
    await page.getByTestId("manual-save-btn").click();
    await expect(page.getByTestId("save-status")).toHaveText(/Saved/i);

    // 13. Reload the browser to verify persistent SQLite storage
    await page.reload();
    await expect(page.getByTestId("designer-page")).toBeVisible();
    await expect(page.getByTestId("shelf-canvas")).toBeVisible();
    await expect(page.locator('[data-testid^="placement-"]').first()).toBeVisible();

    // 14. Open Export Modal
    await page.getByTestId("export-btn").click();
    await expect(page.getByText("Export Planogram Layout")).toBeVisible();
    await expect(page.getByTestId("export-png-btn")).toBeVisible();
    await expect(page.getByTestId("export-json-btn")).toBeVisible();

    // 15. Verify JSON export content from backend
    const currentUrl = page.url();
    const idMatch = currentUrl.match(/id=(\d+)/);
    expect(idMatch).toBeTruthy();
    const planogramId = idMatch![1];

    const exportRes = await request.get(`http://localhost:8000/api/v1/planograms/${planogramId}/export.json`);
    expect(exportRes.ok()).toBeTruthy();
    const exportJson = await exportRes.json();
    expect(exportJson.format_version).toBe("1.0");
    expect(exportJson.unit).toBe("cm");
    expect(exportJson.shelves.length).toBeGreaterThan(0);
    expect(exportJson.shelves[0].width_cm).toBe(120);
    expect(exportJson.shelves[0].placements.length).toBeGreaterThan(0);
    expect(exportJson.shelves[0].placements[0].product_width_cm).toBeGreaterThan(0);
  });
});
