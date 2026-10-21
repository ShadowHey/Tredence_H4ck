import { test, expect } from "@playwright/test";

test.describe("Individual cutout downloads", () => {
  test("downloads the exact visible crop without a fetch error", async ({ page }) => {
    await page.goto("http://localhost:3000/analysis?outputId=3");
    await expect(page.getByTestId("analysis-page")).toBeVisible();
    await page.getByTestId("open-cutouts-btn").click();
    await expect(page.getByTestId("cutout-viewer-modal")).toBeVisible();

    const firstDownload = page.getByRole("link", { name: "Download cutout #1", exact: true });
    await expect(firstDownload).toBeVisible();
    const download = page.waitForEvent("download");
    await firstDownload.click();
    const downloadedFile = await download;
    expect(downloadedFile.suggestedFilename()).toMatch(/\.jpg$/);
    await expect(page.getByText("Failed to fetch")).toHaveCount(0);
  });
});
