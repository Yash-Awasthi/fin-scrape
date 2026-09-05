# Render Deployment Configuration

This guide explains how to configure your Brown Man Bunker deployment on Render.com for live data access.

## Environment Variables

To enable live data collection, add these environment variables in your Render dashboard:

### Required API Keys

1. **FRED_API_KEY**
   - Value: `91c1cb50df4e3f061389ac2ecc335ead`
   - Used for: Treasury volatility, Jobless claims, Labor displacement data
   - Source: Federal Reserve Economic Data

2. **NEWS_API_KEY**
   - Value: `88dd145bb61d4aa0b9655edec04309f8`
   - Used for: Taiwan zone and Hormuz risk monitoring
   - Source: News API for geopolitical events

3. **ALPHA_VANTAGE_API_KEY**
   - Value: `H1UKYU1N148IZ94W`
   - Used for: Luxury goods collapse index
   - Source: Alpha Vantage financial data

## How to Add Environment Variables in Render

1. Go to your Render dashboard
2. Click on your web service
3. Navigate to the **Environment** tab
4. Click **Add Environment Variable**
5. Add each key-value pair:
   - Key: `FRED_API_KEY`
   - Value: `91c1cb50df4e3f061389ac2ecc335ead`
6. Repeat for all three API keys
7. Click **Save Changes**
8. Render will automatically redeploy with the new configuration

## Verifying Live Data

After deployment, your dashboard should show:
- **LIVE** badges next to indicators using real data
- Real-time values for:
  - Treasury Volatility (FRED)
  - Jobless Claims (FRED)
  - Labor Displacement (FRED)
  - Luxury Collapse Index (Alpha Vantage - during market hours)
  - Taiwan/Hormuz news monitoring (if events detected)

## Indicators Requiring Manual Input

These indicators still need manual updates via the dashboard:
- ICE Detention rates
- DoD AI Autonomy status
- mBridge settlement share
- Pharmacy shortages (or use "Scrape FDA" button)
- School closures
- AGI milestones

Access manual input at: `https://your-app.onrender.com/manual-input`

## Build Configuration

Your Render service should have:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `cd dashboard && python app.py`
- **Auto-Deploy**: Enabled for main branch

## Monitoring Deployment

Check deployment status:
1. **Events** tab shows deployment history
2. **Logs** tab shows real-time application logs
3. Look for "Starting Household Resilience Dashboard" in logs

## Troubleshooting

If live data isn't working:
1. Check Logs tab for API errors
2. Verify environment variables are set correctly
3. Ensure API keys haven't expired
4. Check API rate limits (especially News API free tier)