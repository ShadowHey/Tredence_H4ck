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

  test("opens the labeled shelf fixture's selected planogram compliance report", async ({ page, request }) => {
    const outputsResponse = await request.get("http://localhost:8000/api/v1/outputs");
    expect(outputsResponse.ok()).toBeTruthy();
    const outputs = await outputsResponse.json();
    const fixtureOutput = outputs.find((item: { source_filename: string; planogram_name?: string }) =>
      item.source_filename === "bc_image1.png" && item.planogram_name === "Pipeline Verification Planogram");
    expect(fixtureOutput, "labeled shelf fixture output linked to its selected planogram").toBeTruthy();
    if (!fixtureOutput) throw new Error("Expected the labeled shelf fixture output to exist.");

    const reportResponse = await request.get(`http://localhost:8000/api/v1/outputs/${fixtureOutput.id}/compliance`);
    expect(reportResponse.ok()).toBeTruthy();
    const report = await reportResponse.json();
    expect(report.output_id).toBe(fixtureOutput.id);
    expect(report.audit_snapshot_sha256).toBe(fixtureOutput.audit_snapshot.snapshot_sha256);
    expect(report.issues.map((issue: { type: string }) => issue.type)).toEqual([
      "misplaced_product", "empty_space",
    ]);
    expect(report.summary.misplaced_product).toBe(1);
    expect(report.summary.empty_space).toBe(1);
    expect(report.summary.needs_review).toBe(0);
    expect(report.layout_comparison.rows.map((row: { expected_facings: Array<{ sku: string }> }) =>
      row.expected_facings[0]?.sku)).toEqual(["BEV-200", "BEV-201", "BEV-202", "BEV-203"]);

    await page.goto(`/analysis?outputId=${fixtureOutput.id}`);
    await expect(page.getByTestId("analysis-page")).toBeVisible();
    await expect(page.getByTestId("compliance-report")).toBeVisible();
    await expect(page.getByTestId("normalized-layout-comparison")).toContainText("Row 4");
    await expect(page.getByTestId("audit-status")).toBeVisible();
    const findings = page.getByTestId("compliance-issue");
    await expect(findings).toHaveCount(2);
    await expect(findings.nth(0)).toContainText("Move Yellow Lays from Row 1 to its designated Row 2 location");
    await expect(findings.nth(1)).toContainText("Fill the empty facing in Row 2 with Yellow Lays");
  });
});
