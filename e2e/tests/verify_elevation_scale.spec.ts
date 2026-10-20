import { test, expect } from "@playwright/test";
import path from "path";

const ARTIFACT_DIR = "/Users/dhruv/.gemini/antigravity-ide/brain/a392ed68-b77d-43a0-9d68-3ae758d8881a";

test("Verify 1:1 elevation scale alignment across 8 shelf rows", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 950 });

  // 1. Go to dashboard and create a fresh planogram to test 8 rows
  await page.goto("http://localhost:3000/");
  await page.waitForSelector('[data-testid="dashboard-page"]');
  await page.getByTestId("create-planogram-btn").click();
  await page.fill('input[placeholder*="Beverages Gondola"]', "8-Row Scale Verification Planogram");
  await page.getByRole("button", { name: "Start Designing" }).click();

  // 2. Wait for designer to load
  await page.waitForURL(/\/designer\?id=\d+/);
  await page.waitForSelector('[data-testid="designer-page"]');

  // 3. Click Add Shelf
  await page.getByTestId("canvas-add-shelf-btn").click();
  await expect(page.getByText("Add New Shelf Unit")).toBeVisible();

  // Fill in 8 rows
  await page.fill('input[value="Shelf 01"]', "8-Tier Bay Fixture");
  // Change row count to 8 via number input
  await page.getByTestId("input-modal-shelf-row-count-number").fill("8");

  await page.getByTestId("modal-add-shelf-submit").click();

  // 4. Confirm shelf canvas renders
  await page.waitForSelector('[data-testid="shelf-canvas"]');
  await page.waitForSelector('[data-testid="shelf-row-7"]'); // 8 rows: index 0 to 7

  // 5. Open Product Library and add a product
  await page.getByTestId("tab-library").click();
  await page.waitForSelector('[data-testid="product-library-panel"]');

  const addProductBtn = page.locator('[data-testid^="catalogue-product-"]').first().getByRole("button", { name: /Add/i });
  if (await addProductBtn.isVisible()) {
    await addProductBtn.click();
  }

  // 6. Verify mathematical alignment of all 8 row brackets with shelf row bays
  for (let r = 0; r < 8; r++) {
    const rowPair = page.locator(`[data-testid="shelf-row-${r}"]`).locator("xpath=..");
    const bracket = rowPair.locator("div").first();
    const shelfBay = page.locator(`[data-testid="shelf-row-${r}"]`);

    const bracketBox = await bracket.boundingBox();
    const shelfBayBox = await shelfBay.boundingBox();

    expect(bracketBox).not.toBeNull();
    expect(shelfBayBox).not.toBeNull();

    // Verify top alignment within 1px
    expect(Math.abs(bracketBox!.y - shelfBayBox!.y)).toBeLessThanOrEqual(1.5);
    // Verify height match within 1px
    expect(Math.abs(bracketBox!.height - shelfBayBox!.height)).toBeLessThanOrEqual(1.5);

    // Verify row label R{r+1} text exists in bracket
    await expect(bracket).toContainText(`R${r + 1}`);
    await expect(bracket).toContainText("20.6 cm");
  }

  // 7. Verify plinth fixture alignment
  await expect(page.getByText("Base Plinth Fixture (15 cm)")).toBeVisible();
  await expect(page.getByText("Total 180cm")).toBeVisible();

  // 8. Capture screenshots for visual confirmation
  const canvasTarget = page.locator("#planogram-render-target");
  await canvasTarget.screenshot({ path: path.join(ARTIFACT_DIR, "elevation_scale_8_rows_canvas.png") });
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "elevation_scale_8_rows_fullpage.png") });
});
