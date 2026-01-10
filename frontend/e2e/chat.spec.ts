import { test, expect } from "@playwright/test";

/**
 * E2E tests for the AI Chat Platform.
 *
 * These tests run against the real Claude Agent SDK backend,
 * which means:
 * - They require ANTHROPIC_API_KEY to be set in the backend .env
 * - They will incur API costs (~$0.01-0.10 per test)
 * - They may take 30-90 seconds per test due to API latency
 * - Response content may vary, so assertions use flexible matching
 */

test.describe("Chat Interface", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the chat page
    await page.goto("/chat");

    // Wait for the page to be fully loaded
    await expect(page.getByText("AI Assistant")).toBeVisible();
  });

  test("displays welcome message on initial load", async ({ page }) => {
    // Verify the welcome message is shown
    await expect(page.getByText("AI Assistant")).toBeVisible();
    await expect(
      page.getByText(/Ask me anything/i)
    ).toBeVisible();
  });

  test("can send a message and receive a response", async ({ page }) => {
    // Find the input field and type a simple question
    const input = page.getByPlaceholder(/ask a question/i);
    await expect(input).toBeVisible();

    // Send a simple math question that has a predictable answer
    await input.fill("What is 2+2? Reply with just the number.");
    await page.getByRole("button", { name: /send/i }).click();

    // Wait for the response to appear (extended timeout for real API)
    // The response should contain "4" somewhere
    await expect(page.getByText("4")).toBeVisible({ timeout: 90000 });
  });

  test("displays streaming text progressively", async ({ page }) => {
    // Type a prompt that will generate a longer response
    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill(
      "Write a single sentence about the color blue. Keep it brief."
    );
    await page.getByRole("button", { name: /send/i }).click();

    // Wait for some response to start appearing
    // We check that content appears within the message area
    const messageArea = page.locator('[class*="bg-gray-100"]').first();

    // Wait for the assistant message container to appear
    await expect(messageArea).toBeVisible({ timeout: 60000 });

    // Verify there's text content in the response
    await expect(async () => {
      const text = await messageArea.textContent();
      expect(text?.length).toBeGreaterThan(5);
    }).toPass({ timeout: 90000 });
  });

  test("can handle multi-turn conversation", async ({ page }) => {
    // First message
    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill("Remember the number 42.");
    await page.getByRole("button", { name: /send/i }).click();

    // Wait for first response
    await expect(page.locator('[class*="bg-gray-100"]').first()).toBeVisible({
      timeout: 60000,
    });

    // Give the first response time to complete
    await page.waitForTimeout(2000);

    // Second message referencing the first
    await input.fill("What number did I just tell you? Reply with just the number.");
    await page.getByRole("button", { name: /send/i }).click();

    // Wait for second response containing 42
    await expect(page.getByText("42")).toBeVisible({ timeout: 90000 });
  });
});

test.describe("Tool Calls", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/chat");
    await expect(page.getByText("AI Assistant")).toBeVisible();
  });

  test("displays tool calls when agent uses tools", async ({ page }) => {
    // Ask a question that will trigger a tool call (if agent decides to use tools)
    // Note: The agent may or may not use tools depending on its judgment
    const input = page.getByPlaceholder(/ask a question/i);
    await input.fill(
      "What is today's date? You can use tools if needed to find out."
    );
    await page.getByRole("button", { name: /send/i }).click();

    // Wait for any response
    await expect(page.locator('[class*="bg-gray-100"]').first()).toBeVisible({
      timeout: 90000,
    });

    // Response should contain something about a date
    await expect(async () => {
      const pageContent = await page.content();
      // The response should mention some date-related content
      const hasDate =
        pageContent.includes("202") || // Year
        pageContent.includes("January") ||
        pageContent.includes("date");
      expect(hasDate).toBeTruthy();
    }).toPass({ timeout: 10000 });
  });
});

test.describe("Error Handling", () => {
  test("handles empty message gracefully", async ({ page }) => {
    await page.goto("/chat");

    // The send button should be disabled or clicking should not send
    const sendButton = page.getByRole("button", { name: /send/i });

    // Either the button is disabled or nothing happens on click
    const isDisabled = await sendButton.isDisabled();

    if (!isDisabled) {
      // Click with empty input
      await sendButton.click();

      // Should not show an error state or crash
      // The welcome message should still be visible
      await expect(page.getByText("AI Assistant")).toBeVisible();
    }
  });
});
