import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('should show the app title', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('text=国关推演平台')).toBeVisible({ timeout: 15000 })
  })

  test('should navigate to events page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/events"]')
    await expect(page).toHaveURL(/.*events/)
    await expect(page.locator('text=事件')).toBeVisible()
  })

  test('should navigate to analogies page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/analogies"]')
    await expect(page).toHaveURL(/.*analogies/)
    await expect(page.locator('text=历史类比')).toBeVisible()
  })

  test('should navigate to pipeline page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/pipeline"]')
    await expect(page).toHaveURL(/.*pipeline/)
    await expect(page.locator('text=运行分析')).toBeVisible()
  })

  test('should navigate to calibration page', async ({ page }) => {
    await page.goto('/')
    await page.click('a[href="/calibration"]')
    await expect(page).toHaveURL(/.*calibration/)
    await expect(page.locator('text=预测校准')).toBeVisible()
  })
})

test.describe('Language Switch', () => {
  test('should toggle language between Chinese and English', async ({ page }) => {
    await page.goto('/')
    const langBtn = page.locator('button:has-text("中文")')
    if (await langBtn.isVisible()) {
      await langBtn.click()
      await expect(page.locator('button:has-text("EN")')).toBeVisible()
    }
  })
})

test.describe('Theme Switch', () => {
  test('should toggle dark/light mode', async ({ page }) => {
    await page.goto('/')
    const themeBtn = page.locator('button:has-text("Light")')
    if (await themeBtn.isVisible()) {
      await themeBtn.click()
      await expect(page.locator('button:has-text("Dark")')).toBeVisible()
    }
  })
})

test.describe('Events Page', () => {
  test('should show search input', async ({ page }) => {
    await page.goto('/events')
    await expect(page.locator('input[placeholder*="搜索"]')).toBeVisible()
  })

  test('should show type distribution chart when no event selected', async ({ page }) => {
    await page.goto('/events')
    await expect(page.locator('text=事件类型分布')).toBeVisible({ timeout: 10000 })
  })
})

test.describe('Analogies Page', () => {
  test('should show case library', async ({ page }) => {
    await page.goto('/analogies')
    await expect(page.locator('text=历史案例库')).toBeVisible({ timeout: 10000 })
  })

  test('should show add case button', async ({ page }) => {
    await page.goto('/analogies')
    await expect(page.locator('text=新增')).toBeVisible()
  })
})

test.describe('Pipeline Page', () => {
  test('should show run button', async ({ page }) => {
    await page.goto('/pipeline')
    await expect(page.locator('text=启动完整分析')).toBeVisible({ timeout: 10000 })
  })

  test('should show pipeline steps', async ({ page }) => {
    await page.goto('/pipeline')
    await expect(page.locator('text=新闻采集')).toBeVisible()
    await expect(page.locator('text=聚类分析')).toBeVisible()
    await expect(page.locator('text=事件抽象')).toBeVisible()
  })
})
