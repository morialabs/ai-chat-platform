import { test, expect } from "@playwright/test";

/**
 * Simple E2E smoke test for the AI Chat Platform.
 *
 * This test verifies that both frontend and backend are working together:
 * - Frontend serves the chat page
 * - Backend processes messages and returns responses
 *
 * Note: Requires ANTHROPIC_API_KEY in backend/.env
 */

test("can send a message and receive a response", async ({ page }) => {
  // Navigate to chat page (verifies frontend is running)
  await page.goto("/chat");

  // Verify the page loaded
  await expect(page.getByText("AI Assistant")).toBeVisible();

  // Find the input field and send a simple message
  const input = page.getByPlaceholder("Type your message...");
  await expect(input).toBeVisible({ timeout: 10000 });

  await input.fill("Say hello");
  await page.getByRole("button", { name: "Send message" }).click();

  // Wait for a response from the backend (verifies backend is running)
  // Look for any assistant message container with content
  const assistantMessage = page.locator(".bg-gray-100").first();
  await expect(assistantMessage).toBeVisible({ timeout: 90000 });

  // Verify the response has some text content
  await expect(async () => {
    const text = await assistantMessage.textContent();
    expect(text && text.length > 0).toBeTruthy();
  }).toPass({ timeout: 90000 });
});
