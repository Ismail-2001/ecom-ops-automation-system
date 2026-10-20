import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  // Dev-mode Next recompiles routes on first visit; high worker counts
  // overwhelm the single dev server and cause flaky route-navigation
  // timeouts. Two workers keeps the suite deterministic locally.
  workers: process.env.CI ? 1 : 2,
  reporter: [['html', { open: 'never' }], ['list']],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'npm run dev -- -p 3200',
    url: 'http://localhost:3200',
    reuseExistingServer: true,
    timeout: 60_000,
    // `src/lib/session.ts` falls back to a *random per-process* secret when
    // SESSION_SECRET is unset. Next dev evaluates route handlers and client
    // code in separate module graphs, so each graph generated a different
    // key: the login cookie signed by one was rejected by the other and every
    // authenticated navigation bounced back to /login (401 "Not
    // authenticated"). Pin a deterministic dev-only secret so the whole E2E
    // suite gets one shared key. Production still requires SESSION_SECRET and
    // refuses to boot without it.
    env: {
      ...process.env,
      SESSION_SECRET:
        process.env.SESSION_SECRET || 'e2e-dev-session-secret-do-not-use-in-production',
    },
  },
})
