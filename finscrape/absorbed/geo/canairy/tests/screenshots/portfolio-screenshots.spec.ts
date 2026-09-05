import { test, expect } from '@playwright/test';

test.describe('Canairy Portfolio Screenshots', () => {
  
  // Wait for app to load and add some mock data
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(3000); // Wait for initial load
    
    // Wait for key components to be visible
    await expect(page.locator('text=Canairy')).toBeVisible();
    await page.waitForTimeout(2000); // Allow animations to settle
  });

  test('01 - Dashboard Overview', async ({ page }) => {
    await page.screenshot({
      path: 'portfolio-assets/screenshots/01-dashboard-overview.png',
      fullPage: true
    });
  });

  test('02 - Dashboard Hero Section', async ({ page }) => {
    // Focus on the main dashboard area
    await page.screenshot({
      path: 'portfolio-assets/screenshots/02-dashboard-hero.png',
      clip: { x: 256, y: 0, width: 1664, height: 900 }
    });
  });

  test('03 - Critical Indicators Panel', async ({ page }) => {
    const indicatorsPanel = page.locator('[data-testid="critical-indicators"], .bg-\\[\\#111111\\]').first();
    await expect(indicatorsPanel).toBeVisible();
    
    await indicatorsPanel.screenshot({
      path: 'portfolio-assets/screenshots/03-critical-indicators.png'
    });
  });

  test('04 - Priority Actions Panel', async ({ page }) => {
    // Try multiple selectors for Priority Actions
    const selectors = [
      'text=Priority Actions',
      'text=Actionable Priority Actions',
      'h3:has-text("Priority Actions")',
      '.bg-\\[\\#111111\\]:has-text("Priority Actions")'
    ];
    
    let found = false;
    for (const selector of selectors) {
      const element = page.locator(selector).first();
      if (await element.isVisible({ timeout: 1000 }).catch(() => false)) {
        await element.locator('..').locator('..').screenshot({
          path: 'portfolio-assets/screenshots/04-priority-actions.png'
        });
        found = true;
        break;
      }
    }
    
    if (!found) {
      // Fallback: take a screenshot of the general area
      await page.screenshot({
        path: 'portfolio-assets/screenshots/04-priority-actions.png',
        clip: { x: 256, y: 400, width: 1400, height: 600 }
      });
    }
  });

  test('05 - News Sidebar', async ({ page }) => {
    // Open news sidebar
    const newsButton = page.locator('[title="Toggle news sidebar"]');
    if (await newsButton.isVisible()) {
      await newsButton.click();
      await page.waitForTimeout(500);
      
      await page.screenshot({
        path: 'portfolio-assets/screenshots/05-news-sidebar.png',
        fullPage: true
      });
    }
  });

  test('06 - Indicators Page', async ({ page }) => {
    await page.goto('/indicators');
    await page.waitForTimeout(2000);
    
    await page.screenshot({
      path: 'portfolio-assets/screenshots/06-indicators-page.png',
      fullPage: true
    });
  });

  test('07 - Individual Indicator Chart', async ({ page }) => {
    // Try to find a chart element
    const chartElement = page.locator('canvas').first();
    if (await chartElement.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Take screenshot of the chart with some padding
      const box = await chartElement.boundingBox();
      if (box) {
        await page.screenshot({
          path: 'portfolio-assets/screenshots/07-indicator-chart.png',
          clip: {
            x: Math.max(0, box.x - 20),
            y: Math.max(0, box.y - 20),
            width: box.width + 40,
            height: box.height + 40
          }
        });
      }
    } else {
      // Fallback: take a screenshot of an indicator card
      const indicatorCard = page.locator('.rounded-lg.border').first();
      if (await indicatorCard.isVisible()) {
        await indicatorCard.screenshot({
          path: 'portfolio-assets/screenshots/07-indicator-chart.png'
        });
      }
    }
  });

  test('08 - Mobile Responsive View', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 390, height: 844 }); // iPhone 12 Pro
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    await page.screenshot({
      path: 'portfolio-assets/screenshots/08-mobile-dashboard.png',
      fullPage: true
    });
  });

  test('09 - Tablet Responsive View', async ({ page }) => {
    // Test tablet viewport  
    await page.setViewportSize({ width: 768, height: 1024 }); // iPad
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    await page.screenshot({
      path: 'portfolio-assets/screenshots/09-tablet-dashboard.png',
      fullPage: true
    });
  });

  test('10 - Dark Theme Showcase', async ({ page }) => {
    // Capture the dark theme in action
    await page.screenshot({
      path: 'portfolio-assets/screenshots/10-dark-theme.png',
      clip: { x: 0, y: 0, width: 1920, height: 1080 }
    });
  });

});