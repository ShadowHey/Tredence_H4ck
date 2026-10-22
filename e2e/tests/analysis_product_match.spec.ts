import { test, expect } from "@playwright/test";

test.describe("Individual product catalogue matching", () => {
  test("shows each product crop and its closest shelf-catalogue candidate", async ({ page }) => {
    // Output #7 is the calibrated four-product shelf fixture used for this flow.
    await page.goto("/analysis?outputId=7");
    await expect(page.getByTestId("analysis-page")).toBeVisible();

    const productMatchTab = page.getByTestId("filter-product-match-btn");
    await expect(productMatchTab).toBeVisible();
    await productMatchTab.click();

    const matchView = page.getByTestId("product-match-view");
    await expect(matchView).toBeVisible();
    const productItems = matchView.getByTestId("product-match-item");
    await expect.poll(() => productItems.count()).toBeGreaterThan(0);
    await expect(productItems.first().getByText("Raw CLIP similarity")).toBeVisible();
    await expect(productItems.first().getByTestId("product-match-status")).toBeVisible();

    await page.getByTestId("filter-all-btn").click();
    await expect(page.getByTestId("analysis-4-col-table")).toBeVisible();
  });
});
