# 📸 Canairy Portfolio Assets Generation

Automated screenshot and demo generation system using Playwright for creating impressive portfolio materials.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
npm install
npm run playwright:install
```

### 2. Generate All Assets
```bash
# Start dev server first (in separate terminal)
npm run dev

# Then generate all portfolio assets
npm run portfolio
```

## 📁 Generated Assets

### Screenshots (`portfolio-assets/screenshots/`)
- `01-dashboard-overview.png` - Full dashboard view
- `02-dashboard-hero.png` - Main dashboard section
- `03-critical-indicators.png` - Critical indicators panel
- `04-priority-actions.png` - Actionable priority actions
- `05-news-sidebar.png` - Intelligent news sidebar
- `06-indicators-page.png` - All indicators page
- `07-indicator-chart.png` - Individual chart example
- `08-mobile-dashboard.png` - Mobile responsive view
- `09-tablet-dashboard.png` - Tablet responsive view
- `10-dark-theme.png` - Dark theme showcase

### Interactive Demos (`portfolio-assets/videos/`)
- `dashboard-navigation-trace.zip` - Navigation flow demo
- `interactive-features-trace.zip` - Interactive elements demo
- `responsive-design-trace.zip` - Responsive design showcase

## 🎬 Individual Commands

```bash
# Screenshots only
npm run screenshots

# Interactive demos only
npm run demos

# View recorded traces
npx playwright show-trace portfolio-assets/videos/dashboard-navigation-trace.zip
```

## 📸 Screenshot Features

### Full Page Captures
- **High Resolution**: 1920x1080 desktop screenshots
- **Mobile & Tablet**: Responsive design documentation
- **Full Page**: Complete vertical scroll capture
- **Component Focus**: Individual UI component screenshots

### Interactive Elements
- **Hover States**: Button and card interactions
- **Modal Dialogs**: Indicator detail modals
- **Sidebar States**: News sidebar open/closed
- **Chart Animations**: Data visualization captures

## 🎥 Video/Trace Features

### User Journey Recording
- Complete navigation flows
- Interactive feature demonstrations  
- Responsive design transitions
- Real user behavior simulation

### Trace Analysis
- Step-by-step user actions
- Performance metrics
- Network activity
- Console logs
- Screenshots at each step

## 💡 Converting Traces to GIFs

### Method 1: Online Tool
1. Open https://trace.playwright.dev/
2. Upload your `.zip` trace file
3. Use browser tools to record screen during playback
4. Convert to GIF using online converters

### Method 2: Playwright Trace Viewer + Screen Recording
```bash
# Open trace viewer
npx playwright show-trace portfolio-assets/videos/dashboard-navigation-trace.zip

# Use OBS Studio, QuickTime, or similar to record the playback
# Then convert to GIF
```

### Method 3: FFmpeg (Advanced)
```bash
# If you have video files, convert with ffmpeg
ffmpeg -i video.mp4 -vf "fps=10,scale=800:-1:flags=lanczos" output.gif
```

## 🎨 Portfolio Usage

### README Examples
```markdown
## 🖥️ Dashboard Overview
![Dashboard](./portfolio-assets/screenshots/01-dashboard-overview.png)

## 📱 Mobile Responsive
<img src="./portfolio-assets/screenshots/08-mobile-dashboard.png" width="300">

## ⚡ Interactive Demo
![Navigation Demo](./portfolio-assets/gifs/dashboard-navigation.gif)
```

### Portfolio Website
- Use high-res screenshots for hero sections
- Mobile screenshots for responsive design showcase
- GIFs for interactive feature demonstrations
- Component screenshots for UI/UX detail work

## 🛠️ Customization

### Adding New Screenshots
Edit `tests/screenshots/portfolio-screenshots.spec.ts`:

```typescript
test('Custom Screenshot', async ({ page }) => {
  await page.goto('/your-page');
  await page.waitForTimeout(2000);
  
  await page.screenshot({
    path: 'portfolio-assets/screenshots/custom-shot.png',
    fullPage: true
  });
});
```

### Recording Custom Interactions
Edit `tests/screenshots/interactive-demo.spec.ts`:

```typescript
test('Custom Demo', async ({ page, context }) => {
  await context.tracing.start({ screenshots: true, snapshots: true });
  
  // Your custom interaction flow
  await page.goto('/');
  await page.click('your-selector');
  
  await context.tracing.stop({ path: 'portfolio-assets/videos/custom-demo-trace.zip' });
});
```

## 📊 Asset Optimization

### Image Compression
```bash
# Install imagemin-cli
npm install -g imagemin-cli imagemin-pngquant

# Optimize screenshots
imagemin portfolio-assets/screenshots/*.png --out-dir=portfolio-assets/optimized/ --plugin=pngquant
```

### GIF Optimization
```bash
# Use gifsicle for smaller GIFs
npm install -g gifsicle
gifsicle --optimize=3 input.gif > output.gif
```

## 🎯 Best Practices

### Screenshot Quality
- **Consistent Timing**: Always wait for animations to complete
- **Clean State**: Ensure consistent data/state across screenshots  
- **Multiple Viewports**: Test mobile, tablet, and desktop
- **Dark Theme**: Showcase the professional dark design

### Demo Recording
- **Realistic Timing**: Don't rush interactions
- **Show Features**: Highlight unique functionality
- **Error-Free**: Test flows before recording
- **Performance**: Keep traces under 2MB when possible

### Portfolio Presentation
- **Context**: Explain what each screenshot shows
- **Progressive**: Start with overview, then show details
- **Responsive**: Include mobile views
- **Interactive**: Use GIFs to show functionality

## 🚨 Troubleshooting

### Common Issues

**Screenshots are blank:**
```bash
# Make sure dev server is running
npm run dev

# Wait longer for page load
await page.waitForTimeout(5000);
```

**Trace files too large:**
```bash
# Use shorter recordings
# Focus on specific features
# Reduce viewport size for demos
```

**GIF conversion fails:**
```bash
# Try different online tools
# Use lower frame rate
# Crop to focus area
```

### Debug Mode
```bash
# Run with debug output
DEBUG=pw:api npm run screenshots

# Run in headed mode to see browser
npm run screenshots -- --headed
```

## 📈 Portfolio Impact

### Professional Benefits
- **Visual Portfolio**: Show real functionality, not mockups
- **Technical Skills**: Demonstrate automation and testing
- **Attention to Detail**: Professional screenshot quality
- **User Experience**: Show responsive and interactive design

### Use Cases
- **Job Applications**: Attach screenshots to applications
- **Client Presentations**: Show working software
- **Case Studies**: Document feature development
- **Social Media**: Share development progress

---

*Generated assets showcase the professional quality and sophisticated functionality of the Canairy early warning system.*