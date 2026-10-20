import { test } from "@playwright/test";
import path from "path";

const ARTIFACT_DIR = "/Users/dhruv/.gemini/antigravity-ide/brain/a392ed68-b77d-43a0-9d68-3ae758d8881a";

test("Capture full-resolution UI screenshots", async ({ page }) => {
  // 1. Desktop Viewport (1440x900)
  await page.setViewportSize({ width: 1440, height: 900 });

  // Open Dashboard
  await page.goto("http://localhost:3000/");
  await page.waitForSelector('[data-testid="dashboard-page"]');
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "dashboard_desktop.png") });

  // Open Designer
  await page.goto("http://localhost:3000/designer");
  await page.waitForSelector('[data-testid="designer-page"]');
  // Wait for canvas to load
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "designer_desktop.png") });

  // 2. Narrower Viewport (900x900)
  await page.setViewportSize({ width: 900, height: 900 });
  await page.screenshot({ path: path.join(ARTIFACT_DIR, "designer_narrow.png") });
});
