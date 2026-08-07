import { test, expect } from '@playwright/test'

const BASE = process.env.BASE_URL || 'http://localhost:3200'

test.describe('API Health', () => {
  test('health endpoint returns 200', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/health`)
    expect(resp.ok()).toBeTruthy()
  })

  test('health response includes status field', async ({ request }) => {
    const resp = await request.get(`${BASE}/api/health`)
    const body = await resp.json()
    expect(body).toHaveProperty('status')
  })
})

test.describe('Dashboard Metrics', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addCookies([
      { name: 'opsiq_api_key', value: 'test-key', domain: 'localhost', path: '/' },
      { name: 'opsiq_auth', value: 'true', domain: 'localhost', path: '/' },
    ])
  })

  test('dashboard renders KPI cards', async ({ page }) => {
    await page.goto(`${BASE}/`)
    await expect(page.locator('text=Total Revenue')).toBeVisible()
    await expect(page.locator('text=Decisions Made')).toBeVisible()
    await expect(page.locator('text=Cost Savings')).toBeVisible()
  })

  test('dashboard shows live agent status', async ({ page }) => {
    await page.goto(`${BASE}/`)
    await expect(page.locator('text=Agent Fleet Status')).toBeVisible()
  })
})

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addCookies([
      { name: 'opsiq_api_key', value: 'test-key', domain: 'localhost', path: '/' },
      { name: 'opsiq_auth', value: 'true', domain: 'localhost', path: '/' },
    ])
  })

  test('page has no duplicate IDs on dashboard', async ({ page }) => {
    await page.goto(`${BASE}/`)
    await page.waitForSelector('main', { timeout: 10000 })

    const ids = await page.evaluate(() => {
      const els = document.querySelectorAll('[id]')
      return Array.from(els).map(el => el.id)
    })
    const dupes = ids.filter((id, i) => ids.indexOf(id) !== i)
    expect(dupes).toEqual([])
  })

  test('login form is keyboard-navigable', async ({ page }) => {
    await page.goto(`${BASE}/login`)
    const input = page.locator('input[type="password"]')
    await input.focus()
    expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('INPUT')
  })
})
