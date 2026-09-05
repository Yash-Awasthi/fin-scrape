#!/usr/bin/env node

/**
 * Portfolio Asset Generation Script
 * Generates screenshots and videos for Canairy dashboard
 */

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';

console.log('🎨 Generating Canairy Portfolio Assets...\n');

// Ensure directories exist
const dirs = [
  'portfolio-assets/screenshots',
  'portfolio-assets/videos',
  'portfolio-assets/gifs'
];

dirs.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`📁 Created directory: ${dir}`);
  }
});

async function runCommand(command, description) {
  console.log(`🔄 ${description}...`);
  try {
    execSync(command, { stdio: 'inherit' });
    console.log(`✅ ${description} completed\n`);
  } catch (error) {
    console.log(`❌ ${description} failed:`, error.message);
    console.log('');
  }
}

async function main() {
  // 1. Install browsers if needed
  await runCommand('npx playwright install chromium', 'Installing Playwright browsers');
  
  // 2. Generate screenshots
  await runCommand('npx playwright test tests/screenshots/portfolio-screenshots.spec.ts --headed', 'Generating portfolio screenshots');
  
  // 3. Generate interactive demos with video
  await runCommand('npx playwright test tests/screenshots/interactive-demo.spec.ts --headed', 'Recording interactive demos');
  
  // 4. List generated assets
  console.log('📸 Generated Assets:');
  console.log('===================');
  
  // List screenshots
  const screenshotDir = 'portfolio-assets/screenshots';
  if (fs.existsSync(screenshotDir)) {
    const screenshots = fs.readdirSync(screenshotDir).filter(f => f.endsWith('.png'));
    screenshots.forEach(file => {
      console.log(`   📸 ${file}`);
    });
  }
  
  // List videos
  const videoDir = 'portfolio-assets/videos';
  if (fs.existsSync(videoDir)) {
    const videos = fs.readdirSync(videoDir).filter(f => f.endsWith('.zip'));
    videos.forEach(file => {
      console.log(`   🎬 ${file}`);
    });
  }
  
  console.log('\n🎉 Portfolio asset generation complete!');
  console.log('\n📋 Usage Instructions:');
  console.log('======================');
  console.log('Screenshots: Ready to use in portfolio/README');
  console.log('Trace files: Open with "npx playwright show-trace [file.zip]"');
  console.log('To convert traces to GIFs: Use online tools or ffmpeg');
  
  console.log('\n💡 Pro Tips:');
  console.log('- Optimize PNG files: npx imagemin portfolio-assets/screenshots/*.png --out-dir=optimized/');
  console.log('- Create GIFs from traces: Use https://trace.playwright.dev/ to view and export');
  console.log('- For GitHub README: Use relative paths like ./portfolio-assets/screenshots/01-dashboard-overview.png');
}

main().catch(console.error);