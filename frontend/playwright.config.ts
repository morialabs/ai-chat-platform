import { defineConfig, devices } from "@playwright/test";

// Port configuration from environment variables with defaults
const frontendPort = process.env.PORT || "3000";
const backendPort = process.env.BACKEND_PORT || "8000";

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
    baseURL: `http://localhost:${frontendPort}`,
    // Collect trace on first retry for debugging
    trace: "retain-on-failure",
    // Screenshot on failure
    screenshot: "only-on-failure",
  },
  // Configure both frontend and backend servers to start automatically
  webServer: [
    {
      // In CI, uvicorn is installed globally via pip; locally, it's in the venv
      command: process.env.CI
        ? `cd ../backend && uvicorn src.main:app --host 0.0.0.0 --port ${backendPort}`
        : `cd ../backend && venv/bin/uvicorn src.main:app --host 0.0.0.0 --port ${backendPort}`,
      url: `http://localhost:${backendPort}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: `pnpm dev --port ${frontendPort}`,
      url: `http://localhost:${frontendPort}`,
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
