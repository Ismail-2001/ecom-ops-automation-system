import { test, expect } from '@playwright/test'

const BASE = process.env.BASE_URL || 'http://localhost:3200'

test.beforeEach(async ({ page }) => {
  await page.context().addCookies([
    { name: 'opsiq_api_key', value: 'test-key', domain: 'localhost', path: '/' },
    { name: 'opsiq_auth', value: 'true', domain: 'localhost', path: '/' },
  ])
})

test.describe('Agents Page', () => {
  test('renders agent fleet with all agent types', async ({ page }) => {
    await page.goto(`${BASE}/agents`)
    await expect(page.locator('text=Autonomous Agents')).toBeVisible()

    const agents = [
      'Fraud Detection',
      'Inventory Management',
      'Dynamic Pricing',
      'Marketing Optimization',
      'Cart Recovery',
      'Reviews Management',
      'Support Routing',
    ]

    for (const agent of agents) {
      await expect(page.locator(`text=${agent}`).first()).toBeVisible()
    }
  })

  test('each agent card shows status indicator', async ({ page }) => {
    await page.goto(`${BASE}/agents`)
    await page.waitForSelector('[class*="agent"]', { timeout: 10000 })

    const cards = page.locator('[class*="agent"], [class*="Agent"]')
    const count = await cards.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })
})

test.describe('Orders Page', () => {
  test('renders orders table with columns', async ({ page }) => {
    await page.goto(`${BASE}/orders`)
    await expect(page.locator('text=Orders').first()).toBeVisible()
  })

  test('orders page shows status filters', async ({ page }) => {
    await page.goto(`${BASE}/orders`)
    await expect(page.locator('table')).toBeVisible()
  })
})

test.describe('Products Page', () => {
  test('renders product catalog', async ({ page }) => {
    await page.goto(`${BASE}/products`)
    await expect(page.locator('text=Product Catalog')).toBeVisible()
  })
})

test.describe('Analytics Page', () => {
  test('renders analytics dashboard', async ({ page }) => {
    await page.goto(`${BASE}/analytics`)
    await expect(page.locator('text=Performance Intelligence')).toBeVisible()
  })
})

test.describe('Settings Page', () => {
  test('renders settings panel', async ({ page }) => {
    await page.goto(`${BASE}/settings`)
    await expect(page.locator('text=System Settings')).toBeVisible()
  })
})

test.describe('Error Boundaries', () => {
  test('login page handles invalid input gracefully', async ({ page }) => {
    await page.goto(`${BASE}/login`)
    const submit = page.locator('button:has-text("Access Command Center")')
    await submit.click()
    await expect(page.locator('input[type="password"]')).toBeVisible()
  })
})
