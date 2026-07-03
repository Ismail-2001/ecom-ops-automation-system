import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('renders the login page at /login', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('text=OpsIQ')).toBeVisible()
    await expect(page.locator('text=Enter API Key')).toBeVisible()
  })

  test('renders the dashboard at /', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Command Center')).toBeVisible()
  })

  test('sidebar navigation links are visible', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=Dashboard')).toBeVisible()
    await expect(page.locator('text=Agents')).toBeVisible()
    await expect(page.locator('text=Orders')).toBeVisible()
    await expect(page.locator('text=Analytics')).toBeVisible()
  })

  test('navigates to agents page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/agents"]')
    await expect(page).toHaveURL('/agents')
    await expect(page.locator('text=Autonomous Agents')).toBeVisible()
  })

  test('navigates to orders page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/orders"]')
    await expect(page).toHaveURL('/orders')
    await expect(page.locator('text=Order Intelligence')).toBeVisible()
  })

  test('navigates to analytics page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/analytics"]')
    await expect(page).toHaveURL('/analytics')
    await expect(page.locator('text=Performance Intelligence')).toBeVisible()
  })

  test('navigates to products page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/products"]')
    await expect(page).toHaveURL('/products')
    await expect(page.locator('text=Product Catalog')).toBeVisible()
  })

  test('navigates to security page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/security"]')
    await expect(page).toHaveURL('/security')
    await expect(page.locator('text=Security Operations')).toBeVisible()
  })

  test('navigates to settings page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/settings"]')
    await expect(page).toHaveURL('/settings')
    await expect(page.locator('text=System Settings')).toBeVisible()
  })
})

test.describe('404 Page', () => {
  test('shows 404 for unknown routes', async ({ page }) => {
    await page.goto('/nonexistent-page')
    await expect(page.locator('text=Page Not Found')).toBeVisible()
    await expect(page.locator('text=404')).toBeVisible()
  })
})
