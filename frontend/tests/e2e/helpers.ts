import { expect, type Page } from '@playwright/test'

const API_KEY = process.env.OPSIQ_API_KEY || 'opsiq-dev-key-2024'

/**
 * Log in via the real BFF flow so the HttpOnly `opsiq_session` cookie is
 * issued server-side (same as a real user). Returns true on success.
 */
export async function loginAs(page: Page, apiKey: string = API_KEY): Promise<void> {
  await page.goto('/login')
  const input = page.locator('input[type="password"]')
  const submit = page.locator('button:has-text("Access Command Center")')
  await input.waitFor({ state: 'visible' })

  // WebKit can receive the first fill before React hydration replaces the
  // shell input (value silently wiped -> submit stays disabled). Refill until
  // the value sticks and the submit button reacts to it.
  for (let attempt = 0; attempt < 3; attempt++) {
    await input.fill(apiKey)
    if ((await input.inputValue()) === apiKey && (await submit.isEnabled())) break
  }
  await expect(input).toHaveValue(apiKey)
  await expect(submit).toBeEnabled()

  await submit.click()
  await page.waitForURL('**/', { timeout: 15_000 })
  await expect(page.locator('text=Command Center').first()).toBeVisible()
}