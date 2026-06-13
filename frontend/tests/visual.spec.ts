import { expect, test } from "@playwright/test";

test("workbench renders without obvious overlap on desktop and mobile", async ({ page }) => {
  await page.goto("http://localhost:3000");
  await expect(page.getByText("Stu-Bench Demo")).toBeVisible();

  await page.setViewportSize({ width: 1280, height: 800 });
  await expect(page.locator(".columns")).toBeVisible();
  await expect(page).toHaveScreenshot("workbench-desktop-light.png", { fullPage: true });

  await page.getByRole("button", { name: "Toggle theme" }).click();
  await expect(page).toHaveScreenshot("workbench-desktop-dark.png", { fullPage: true });

  await page.setViewportSize({ width: 390, height: 900 });
  await expect(page.locator(".columns")).toBeVisible();
  await expect(page).toHaveScreenshot("workbench-mobile-dark.png", { fullPage: true });
});
