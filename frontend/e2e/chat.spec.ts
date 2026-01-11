import { test, expect } from "@playwright/test";

/**
 * Basic E2E smoke test for the AI Chat Platform.
 *
 * Verifies that frontend and backend are running and the UI renders correctly.
 * This test is intentionally simple and agnostic to UI changes.
 */

test("chat page loads with send button", async ({ page }) => {
  // Navigate to chat page (verifies frontend is running)
  await page.goto("/chat");

  // Verify the page title/header is visible
  await expect(page.getByText("AI Assistant")).toBeVisible();

  // Verify a button exists (send button)
  await expect(page.getByRole("button").first()).toBeVisible();
});
