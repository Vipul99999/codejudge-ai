import { expect, test } from "@playwright/test";

test("loads the evaluator console", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "CodeJudge AI" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Run Evaluation/i })).toBeVisible();
  await page.getByText("Benchmark Dashboard").click();
  await expect(page.getByRole("heading", { name: "Benchmark Dashboard" })).toBeVisible();
});

