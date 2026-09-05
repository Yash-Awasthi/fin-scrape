# Live Data Status

This document shows which indicators are pulling live data vs mock data.

## Currently Live (7 indicators)

1. **Treasury Volatility** ✅
   - Source: FRED API
   - Updates: Daily
   - Requires: FRED_API_KEY

2. **Jobless Claims** ✅
   - Source: FRED API  
   - Updates: Weekly
   - Requires: FRED_API_KEY

3. **Labor Displacement** ✅
   - Source: FRED API
   - Updates: Monthly
   - Requires: FRED_API_KEY

4. **GDP Growth** ✅
   - Source: FRED API
   - Updates: Quarterly
   - Requires: FRED_API_KEY

5. **Grocery CPI** ✅
   - Source: BLS API
   - Updates: Monthly
   - No API key required

6. **CISA Cyber Threats** ✅
   - Source: CISA public JSON feed
   - Updates: Daily
   - No API key required

7. **Grid Outages** ✅
   - Source: DOE OE-417 CSV
   - Updates: As reported
   - No API key required

## Sometimes Live (2 indicators)

8. **Luxury Collapse Index** ⚡
   - Source: Alpha Vantage API
   - Status: Live during market hours, may hit rate limits
   - Requires: ALPHA_VANTAGE_API_KEY

9. **Taiwan/Hormuz News** ⚡
   - Source: News API
   - Status: Limited by free tier (100 requests/day)
   - Requires: NEWS_API_KEY

## Always Mock/Manual (7 indicators)

10. **ICE Detention** ❌
    - Requires: Manual PDF download from ICE website

11. **DoD AI Autonomy** ❌
    - Requires: Manual search of procurement documents

12. **mBridge Currency** ❌
    - Requires: Manual central bank reports

13. **Pharmacy Shortages** ❌
    - Can scrape FDA but requires manual trigger

14. **School Closures** ❌
    - Requires: Local district monitoring

15. **AGI Milestones** ❌
    - Requires: Human judgment on AI progress

16. **Taiwan Exclusion Zone** ❌
    - Part of Taiwan news but needs specific military sources

## Environment Variables for Render

Add these in Render dashboard:
```
FRED_API_KEY=91c1cb50df4e3f061389ac2ecc335ead
NEWS_API_KEY=88dd145bb61d4aa0b9655edec04309f8
ALPHA_VANTAGE_API_KEY=H1UKYU1N148IZ94W
```

## Troubleshooting

If an indicator shows MOCK when it should be LIVE:
1. Check Render logs for API errors
2. Verify environment variables are set
3. Check API rate limits
4. Some APIs may be temporarily down