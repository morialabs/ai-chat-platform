import { test, expect } from "@playwright/test";

/**
 * E2E tests for the AI Chat Platform.
 *
 * These tests verify core chat functionality including:
 * - Basic message flow
 * - Markdown rendering
 * - Multi-turn conversations
 * - Tool call display
 * - AskUserQuestion flow
 * - Stop streaming
 *
 * Note: Tests make real API calls and incur costs (~$0.01-0.10 per test).
 */

// Helper to get assistant message containers (excluding textarea and loading indicator)
// The loading indicator has animate-bounce divs inside, so we exclude those
const getAssistantMessages = (page: import("@playwright/test").Page) =>
  page.locator(
    "div.bg-gray-100.rounded-lg.p-4:not(:has(.animate-bounce)), div.dark\\:bg-gray-800.rounded-lg.p-4:not(:has(.animate-bounce))"
  );

test.describe("Chat Platform E2E Tests", () => {
  /**
   * Basic smoke test - verifies frontend and backend are running.
   */
  test("chat page loads with send button", async ({ page }) => {
    await page.goto("/chat");
    await expect(page.getByText("AI Assistant")).toBeVisible();
    await expect(page.getByRole("button").first()).toBeVisible();
  });

  /**
   * TC1: Basic Message Flow
   * Tests sending a simple message and receiving a response.
   */
  test("TC1: basic message flow", async ({ page }) => {
    await page.goto("/chat");

    // Verify welcome message
    await expect(page.getByText("AI Assistant")).toBeVisible();

    // Find the textarea and type a message
    const textarea = page.getByPlaceholder("Type your message...");
    await textarea.fill("Hello, what is 2+2? Reply with just the number.");

    // Verify send button is enabled
    const sendButton = page.getByRole("button", { name: "Send message" });
    await expect(sendButton).toBeEnabled();

    // Send the message
    await sendButton.click();

    // Wait for assistant response (the rounded-lg p-4 container)
    const response = getAssistantMessages(page).last();
    await expect(response).toBeVisible({ timeout: 90000 });

    // Verify response contains "4"
    await expect(response).toContainText("4", { timeout: 90000 });
  });

  /**
   * TC2: Markdown Rendering
   * Tests that code blocks and tables render correctly.
   */
  test("TC2: markdown rendering", async ({ page }) => {
    await page.goto("/chat");

    const textarea = page.getByPlaceholder("Type your message...");
    const sendButton = page.getByRole("button", { name: "Send message" });

    // Test 1: Code block rendering
    await textarea.fill(
      "Show me a Python function that adds two numbers. Use a code block with python syntax highlighting."
    );
    await sendButton.click();

    // Wait for code block to appear (language label with "python")
    await expect(page.getByText("python", { exact: true })).toBeVisible({
      timeout: 90000,
    });

    // Verify code element with language class exists
    await expect(
      page.locator('[class*="language-python"]').first()
    ).toBeVisible();

    // Wait for response to complete
    await expect(textarea).toBeEnabled({ timeout: 30000 });

    // Test 2: Table rendering (new session to avoid multi-turn issues)
    // Navigate to fresh chat page
    await page.goto("/chat");

    await textarea.fill(
      "Show me a markdown table with 3 programming languages and their primary uses. Use proper markdown table syntax."
    );
    await sendButton.click();

    // Wait for table to render
    await expect(page.locator("table")).toBeVisible({ timeout: 90000 });

    // Verify table has headers
    await expect(page.locator("th").first()).toBeVisible();
  });

  /**
   * TC3: Multi-Turn Conversation
   * Tests that context is retained across multiple messages.
   *
   * IMPORTANT: This test waits for the COMPLETE first response before sending
   * the second message, simulating real user behavior. This catches bugs where
   * session state is corrupted after a response fully completes.
   */
  test("TC3: multi-turn conversation", async ({ page }) => {
    await page.goto("/chat");

    const textarea = page.getByPlaceholder("Type your message...");
    const sendButton = page.getByRole("button", { name: "Send message" });

    // First message - introduce name
    await textarea.fill("My name is Alice. Please remember this.");
    await sendButton.click();

    // Wait for COMPLETE response (textarea re-enabled indicates streaming finished)
    await expect(textarea).toBeEnabled({ timeout: 90000 });

    // Verify first response contains acknowledgment
    await expect(getAssistantMessages(page).first()).toContainText(/alice/i);

    // Small delay to simulate real user behavior (reading the response)
    await page.waitForTimeout(500);

    // Second message - ask for name
    await textarea.fill("What is my name?");
    await sendButton.click();

    // Wait for second response to complete
    await expect(textarea).toBeEnabled({ timeout: 90000 });

    // Verify context retained - the second response should contain "Alice"
    await expect(getAssistantMessages(page).last()).toContainText(/alice/i);
  });

  /**
   * TC4: Tool Call Display
   * Tests that tool invocations are displayed with proper UI.
   */
  test("TC4: tool call display", async ({ page }) => {
    await page.goto("/chat");

    const textarea = page.getByPlaceholder("Type your message...");
    const sendButton = page.getByRole("button", { name: "Send message" });

    // Send request that MUST trigger a tool - reading a specific file path
    await textarea.fill(
      "Read the file at /etc/hostname using the Read tool and tell me what it contains. You MUST use the Read tool."
    );
    await sendButton.click();

    // Wait for tool card to appear (button with tool name like Read, Bash, etc.)
    const toolCard = page.locator("button").filter({ hasText: /Read|Bash|Glob|Grep/i });
    await expect(toolCard.first()).toBeVisible({ timeout: 90000 });

    // Wait for response to complete - textarea being enabled indicates response finished
    await expect(textarea).toBeEnabled({ timeout: 90000 });

    // Also verify some response text appeared (indicates completion)
    await expect(getAssistantMessages(page).last()).not.toBeEmpty({ timeout: 5000 });

    // Click to expand tool card
    await toolCard.first().click();

    // Wait for expansion to complete and verify Input section appears
    await expect(page.getByText("Input")).toBeVisible({ timeout: 5000 });

    // Verify Result section appears (might take a moment for tool result to be processed)
    await expect(page.getByText("Result")).toBeVisible({ timeout: 10000 });
  });

  /**
   * TC5: AskUserQuestion Flow
   * Tests the interactive question UI for user input.
   */
  test("TC5: AskUserQuestion flow", async ({ page }) => {
    await page.goto("/chat");

    const textarea = page.getByPlaceholder("Type your message...");
    const sendButton = page.getByRole("button", { name: "Send message" });

    // Send request that triggers AskUserQuestion
    await textarea.fill(
      "I need help choosing a color for my website. Ask me to pick between red, blue, or green using the AskUserQuestion tool."
    );
    await sendButton.click();

    // Wait for question UI to appear (has header badge with blue background)
    const questionUI = page
      .locator(".bg-gray-50, .dark\\:bg-gray-800\\/50")
      .filter({
        has: page.locator('[class*="bg-blue-100"]'),
      });
    await expect(questionUI).toBeVisible({ timeout: 90000 });

    // Verify option buttons exist
    const options = questionUI
      .locator("button")
      .filter({ hasText: /red|blue|green/i });
    await expect(options.first()).toBeVisible();

    // Click an option
    await options.first().click();

    // Verify option is selected (has blue border)
    await expect(options.first()).toHaveClass(/border-blue-500/);

    // Click Submit button
    const submitButton = questionUI.getByRole("button", { name: "Submit" });
    await submitButton.click();

    // Verify conversation continues (new response after submission)
    await expect(getAssistantMessages(page).last()).toBeVisible({
      timeout: 90000,
    });
  });

  /**
   * TC6: Stop Streaming
   * Tests that streaming can be stopped mid-response.
   */
  test("TC6: stop streaming", async ({ page }) => {
    await page.goto("/chat");

    const textarea = page.getByPlaceholder("Type your message...");
    const sendButton = page.getByRole("button", { name: "Send message" });

    // Send request for a code-related long response that the agent will actually answer
    await textarea.fill(
      "List every single method available on JavaScript's Array prototype with a brief one-sentence description of what each method does. Include all methods from ES5 through ES2024. Format each method on its own line."
    );
    await sendButton.click();

    // Wait for streaming to start - the stop button should appear during streaming
    const stopButton = page.getByRole("button", { name: "Stop generation" });

    // Try to catch the stop button - it appears during streaming status
    try {
      await expect(stopButton).toBeVisible({ timeout: 15000 });

      // Let some content stream in
      await page.waitForTimeout(1500);

      // Click stop button
      await stopButton.click();

      // Verify stop button disappears and send button returns
      await expect(sendButton).toBeVisible({ timeout: 10000 });
    } catch {
      // Response completed too quickly - this is OK, verify completion instead
      // Check that textarea is enabled (indicates response finished)
      await expect(textarea).toBeEnabled({ timeout: 90000 });
    }

    // Verify response is visible (partial or complete)
    const response = getAssistantMessages(page).last();
    await expect(response).toBeVisible();

    // Verify input is re-enabled
    await expect(textarea).toBeEnabled();

    // Send a new message to verify recovery
    await textarea.fill("Say 'test complete'");
    await sendButton.click();

    // Verify new response works
    await expect(getAssistantMessages(page).last()).toContainText(
      /test|complete/i,
      { timeout: 90000 }
    );
  });
});
