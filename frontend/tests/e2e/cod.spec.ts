import { test, expect } from '@playwright/test'
import { loginAs } from './helpers'

const BASE = process.env.BASE_URL || 'http://localhost:3200'

test.beforeEach(async ({ page }) => {
  await loginAs(page)
})

/**
 * The BFF proxies /api/v1/* with a default-deny allowlist and the backend
 * must be running separately from the Next dev server Playwright starts.
 * Probe first so the suite reports a skip instead of a misleading failure.
 */
async function backendReady(page: import('@playwright/test').Page): Promise<boolean> {
  const resp = await page.request.get(`${BASE}/api/v1/cod/health`)
  return resp.ok()
}

test.describe('COD Verification Page', () => {
  test('renders the sanitizer and step-up sections', async ({ page }) => {
    await page.goto(`${BASE}/cod-verification`)

    await expect(page.locator('text=COD Verification').first()).toBeVisible()
    await expect(page.locator('text=Phone Sanitizer').first()).toBeVisible()
    await expect(page.locator('text=OTP Step-Up Challenge').first()).toBeVisible()
    await expect(page.getByTestId('cod-validate-input')).toBeVisible()
    await expect(page.getByTestId('cod-otp-phone')).toBeVisible()
    await expect(page.getByTestId('cod-code-input')).toBeVisible()
  })

  test('is reachable from the sidebar navigation', async ({ page }) => {
    await page.goto(`${BASE}/`)
    await page.waitForSelector('nav a', { timeout: 10_000 })

    await page.getByRole('link', { name: 'COD Verification', exact: true }).click()
    await page.waitForURL('**/cod-verification', { timeout: 10_000 })
    await expect(page).toHaveURL(/\/cod-verification/)
    await expect(page.locator('text=Phone Sanitizer').first()).toBeVisible()
  })

  test('keeps the validate button disabled without a number', async ({ page }) => {
    await page.goto(`${BASE}/cod-verification`)
    await expect(page.getByTestId('cod-validate-button')).toBeDisabled()
  })

  test('renders the health configuration strip', async ({ page }) => {
    test.skip(!(await backendReady(page)), 'backend COD endpoints unavailable')

    await page.goto(`${BASE}/cod-verification`)
    await expect(page.getByTestId('cod-health-metric')).toHaveCount(4)
    await expect(page.locator('text=Delivery Provider')).toBeVisible()
    await expect(page.locator('text=Code Lifetime')).toBeVisible()
    await expect(page.getByTestId('cod-health-error')).toHaveCount(0)
  })
})

test.describe('COD phone validation flow', () => {
  test('normalizes a clean Jazz number to E.164', async ({ page }) => {
    test.skip(!(await backendReady(page)), 'backend COD endpoints unavailable')

    await page.goto(`${BASE}/cod-verification`)
    await page.getByTestId('cod-validate-input').fill('03214567890')
    await page.getByTestId('cod-validate-button').click()

    await expect(page.getByTestId('cod-validation-result')).toBeVisible({
      timeout: 10_000,
    })
    await expect(page.getByTestId('cod-e164')).toHaveText('+923214567890')
    await expect(page.getByTestId('cod-operator')).toHaveText('Jazz')
    await expect(page.locator('text=Allow').first()).toBeVisible()
    await expect(page.getByTestId('cod-risk-signals')).toContainText('None')
  })

  test('flags a suspicious number for the OTP step-up instead of dropping it', async ({
    page,
  }) => {
    test.skip(!(await backendReady(page)), 'backend COD endpoints unavailable')

    await page.goto(`${BASE}/cod-verification`)
    await page.getByTestId('cod-validate-input').fill('03000000000')
    await page.getByTestId('cod-validate-button').click()

    await expect(page.getByTestId('cod-validation-result')).toBeVisible({
      timeout: 10_000,
    })
    await expect(page.locator('text=OTP Step-Up').first()).toBeVisible()
    await expect(page.getByTestId('cod-risk-signals')).toContainText('all_same_digit')
  })

  test('marks an undeliverable number for manual review', async ({ page }) => {
    test.skip(!(await backendReady(page)), 'backend COD endpoints unavailable')

    await page.goto(`${BASE}/cod-verification`)
    await page.getByTestId('cod-validate-input').fill('12345')
    await page.getByTestId('cod-validate-button').click()

    await expect(page.getByTestId('cod-validation-result')).toBeVisible({
      timeout: 10_000,
    })
    await expect(page.locator('text=Manual Review').first()).toBeVisible()
  })

  test('soft-flags malformed input for review instead of ever accepting it', async ({
    page,
  }) => {
    test.skip(!(await backendReady(page)), 'backend COD endpoints unavailable')

    await page.goto(`${BASE}/cod-verification`)
    await page.getByTestId('cod-validate-input').fill('not-a-phone')
    await page.getByTestId('cod-validate-button').click()

    // The sanitizer never hard-drops: a 200 with action=review is the design.
    await expect(page.getByTestId('cod-validation-result')).toBeVisible({
      timeout: 10_000,
    })
    await expect(page.locator('text=Manual Review').first()).toBeVisible()
    await expect(page.getByTestId('cod-risk-signals')).toContainText('invalid_format')
    await expect(page.getByTestId('cod-validation-error')).toHaveCount(0)
  })

  test('surfaces a validation failure instead of silently clearing the form', async ({
    page,
  }) => {
    // Inject a deterministic backend failure (real 4xx), since the sanitizer
    // itself answers 200 for bad input by design.
    await page.route('**/api/v1/cod/phone/validate', (route) =>
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'phone number rejected' }),
      }),
    )

    await page.goto(`${BASE}/cod-verification`)
    await page.getByTestId('cod-validate-input').fill('03214567890')
    await page.getByTestId('cod-validate-button').click()

    await expect(page.getByTestId('cod-validation-error')).toBeVisible({
      timeout: 10_000,
    })
    await expect(page.getByTestId('cod-validation-error')).toContainText(
      'phone number rejected',
    )
    await expect(page.getByTestId('cod-validation-result')).toHaveCount(0)
  })
})

test.describe('COD OTP step-up flow', () => {
  test('issues a code without ever exposing the passcode to the UI', async ({ page }) => {
    test.skip(!(await backendReady(page)), 'backend COD endpoints unavailable')

    await page.goto(`${BASE}/cod-verification`)
    await page.getByTestId('cod-otp-phone').fill('03214567890')
    await page.getByTestId('cod-otp-send').click()

    await expect(page.getByTestId('cod-otp-result')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('text=Sent').first()).toBeVisible()

    // The 6-digit passcode must never reach the DOM.
    const body = (await page.locator('body').innerText()).replace(/\s+/g, '')
    expect(body).not.toMatch(/\b\d{6}\b/)
  })

  test('rejects a wrong code and preserves the attempt budget', async ({ page }) => {
    test.skip(!(await backendReady(page)), 'backend COD endpoints unavailable')

    await page.goto(`${BASE}/cod-verification`)
    await page.getByTestId('cod-otp-phone').fill('03214567890')
    await page.getByTestId('cod-otp-send').click()
    await expect(page.getByTestId('cod-otp-result')).toBeVisible({ timeout: 10_000 })

    // Deliberately wrong code; must be refused, never silently accepted.
    await page.getByTestId('cod-code-input').fill('000000')
    await page.getByTestId('cod-verify-button').click()

    await expect(page.getByTestId('cod-verify-result')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('text=Rejected').first()).toBeVisible()
    await expect(page.locator('text=attempts left').first()).toBeVisible()
  })

  test('sends the Roman Urdu template when that language is selected', async ({ page }) => {
    test.skip(!(await backendReady(page)), 'backend COD endpoints unavailable')

    await page.goto(`${BASE}/cod-verification`)
    await page.getByRole('tab', { name: 'Roman Urdu' }).or(page.getByText('Roman Urdu', { exact: true })).first().click()
    await page.getByTestId('cod-otp-phone').fill('03214567890')
    await page.getByTestId('cod-otp-send').click()

    await expect(page.getByTestId('cod-otp-result')).toBeVisible({ timeout: 10_000 })
    await expect(page.locator('text=Sent').first()).toBeVisible()
  })
})
