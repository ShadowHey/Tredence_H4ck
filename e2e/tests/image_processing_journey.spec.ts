import path from "node:path";
import { test, expect } from "@playwright/test";

test.describe("ShelfSense AI image intake and annotated outputs", () => {
  test("assigns one uploaded shelf image to a planogram shelf, processes it, exports it, and deletes the output", async ({ page, request }) => {
    test.setTimeout(120_000);
    const unique = `E2E Image Audit ${Date.now()}`;
    const planogram = await request.post("http://localhost:8000/api/v1/planograms", { data: { name: unique } });
    expect(planogram.ok()).toBeTruthy();
    const planogramData = await planogram.json();
    const shelf = await request.post(`http://localhost:8000/api/v1/planograms/${planogramData.id}/shelves`, {
      data: { name: "E2E Reference Shelf", width_cm: 120, total_height_cm: 180, depth_cm: 40, row_count: 4 },
    });
    expect(shelf.ok()).toBeTruthy();
    const shelfData = await shelf.json();

    await page.goto("http://localhost:3000/input-images");
    await expect(page.getByTestId("input-images-page")).toBeVisible();
    await page.locator('input[type="file"]').setInputFiles(path.resolve("../image-parsing/sample_inputs/test_image.jpg"));
    await expect(page.getByText("test_image.jpg").first()).toBeVisible();
    await page.getByLabel("Planogram").selectOption(String(planogramData.id));
    await page.getByLabel("Shelf").selectOption(String(shelfData.id));
    await expect(page.getByText(/E2E Reference Shelf: 120 cm × 180 cm/i)).toBeVisible();
    await page.getByRole("button", { name: "Process this image" }).click();
    await expect(page.getByText(/Processed successfully/i)).toBeVisible({ timeout: 100_000 });

    await page.goto("http://localhost:3000/outputs");
    await expect(page.getByTestId("outputs-page")).toBeVisible();
    const outputCard = page.locator("article").filter({ hasText: "test_image.jpg" }).first();
    await expect(outputCard).toContainText(unique);
    await expect(outputCard).toContainText("E2E Reference Shelf");
    await outputCard.getByRole("checkbox").check();
    const download = page.waitForEvent("download");
    await page.getByRole("button", { name: "Export" }).click();
    await (await download).cancel();
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Delete" }).click();
    await expect(outputCard).toHaveCount(0);
  });
});
