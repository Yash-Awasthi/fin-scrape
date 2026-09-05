import { test } from '@playwright/test';

test.describe('Canairy Interactive Demos', () => {
  
  test('Demo 01 - Dashboard Navigation Flow', async ({ page, context }) => {
    // Start recording
    await context.tracing.start({ screenshots: true, snapshots: true });
    
    await page.goto('/');
    await page.waitForTimeout(2000);

    // Simulate user interaction flow
    console.log('🎬 Recording: Dashboard navigation...');
    
    // 1. Show main dashboard
    await page.waitForTimeout(1500);
    
    // 2. Click on indicators
    const indicatorCard = page.locator('.rounded-lg.border').first();
    if (await indicatorCard.isVisible()) {
      await indicatorCard.hover();
      await page.waitForTimeout(500);
      await indicatorCard.click();
      await page.waitForTimeout(1000);
    }
    
    // 3. Navigate to indicators page
    await page.click('text=Indicators');
    await page.waitForTimeout(2000);
    
    // 4. Back to dashboard
    await page.click('text=Dashboard');
    await page.waitForTimeout(1500);
    
    // 5. Open news sidebar
    const newsButton = page.locator('[title="Toggle news sidebar"]');
    if (await newsButton.isVisible()) {
      await newsButton.click();
      await page.waitForTimeout(1500);
      
      // Scroll through news
      await page.locator('[data-testid="news-sidebar"]').scroll({ x: 0, y: 200 });
      await page.waitForTimeout(1000);
      
      // Close sidebar
      await newsButton.click();
      await page.waitForTimeout(500);
    }
    
    await context.tracing.stop({ path: 'portfolio-assets/videos/dashboard-navigation-trace.zip' });
  });

  test('Demo 02 - Interactive Features', async ({ page, context }) => {
    await context.tracing.start({ screenshots: true, snapshots: true });
    
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    console.log('🎬 Recording: Interactive features...');
    
    // 1. Hover over different elements
    const statusBar = page.locator('text=NORMAL').first();
    if (await statusBar.isVisible()) {
      await statusBar.hover();
      await page.waitForTimeout(800);
    }
    
    // 2. Interact with priority actions
    const actionCheckbox = page.locator('input[type="checkbox"]').first();
    if (await actionCheckbox.isVisible()) {
      await actionCheckbox.check();
      await page.waitForTimeout(1000);
      await actionCheckbox.uncheck();
      await page.waitForTimeout(500);
    }
    
    // 3. Click resource buttons
    const phoneButton = page.locator('text=FDIC Hotline').first();
    if (await phoneButton.isVisible()) {
      await phoneButton.hover();
      await page.waitForTimeout(1000);
    }
    
    await context.tracing.stop({ path: 'portfolio-assets/videos/interactive-features-trace.zip' });
  });

  test('Demo 03 - Responsive Design', async ({ page, context }) => {
    await context.tracing.start({ screenshots: true, snapshots: true });
    
    console.log('🎬 Recording: Responsive design...');
    
    // Desktop view
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await page.waitForTimeout(2000);
    
    // Tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(1500);
    
    // Mobile view
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(1500);
    
    // Scroll on mobile
    await page.mouse.wheel(0, 500);
    await page.waitForTimeout(1000);
    
    // Back to desktop
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(1000);
    
    await context.tracing.stop({ path: 'portfolio-assets/videos/responsive-design-trace.zip' });
  });

});