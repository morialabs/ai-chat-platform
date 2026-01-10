import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for AI Chat Platform E2E tests.
 *
 * These tests run against the real Claude Agent SDK backend,
 * so they require ANTHROPIC_API_KEY to be set and will incur API costs.
 */
export default defineConfig({
  testDir: "./e2e",
  // Run tests sequentially - real API calls should not be parallelized
  fullyParallel: false,
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
  // No retries for real API tests - they're not flaky, just slow
  retries: 0,
  // Single worker to control costs and avoid rate limiting
  workers: 1,
  // Reporter to use
  reporter: "html",
  // Extended timeout for agent responses (2 minutes)
  timeout: 120000,
  // Shared settings for all projects
  use: {
    // Base URL for the frontend
    baseURL: "http://localhost:3000",
    // Collect trace on first retry for debugging
    trace: "retain-on-failure",
    // Screenshot on failure
    screenshot: "only-on-failure",
  },
  // Configure both frontend and backend servers to start automatically
  webServer: [
    {
      command:
        "cd ../backend && venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000",
      url: "http://localhost:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: "pnpm dev",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
      stdout: "pipe",
      stderr: "pipe",
    },
  ],
  // Configure projects for different browsers
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
