# Adding New Indicators to Your Monitor

## Quick Start

To add the 4 new indicators (Jobless Claims, Luxury Collapse, Pharmacy Shortage, School Closures):

### 1. Update Main Script

Edit `src/main.py` to import and use the new collectors:

```python
# Add to imports
from collectors import (
    TreasuryCollector,
    ICEDetentionCollector, 
    TaiwanZoneCollector,
    HormuzRiskCollector,
    DoDAutonomyCollector,
    MBridgeCollector,
    JoblessClaimsCollector,      # NEW
    LuxuryCollapseCollector,     # NEW
    PharmacyShortageCollector,   # NEW
    SchoolClosureCollector       # NEW
)

# Add to collectors list
collectors = [
    TreasuryCollector(config),
    ICEDetentionCollector(config),
    TaiwanZoneCollector(config),
    HormuzRiskCollector(config),
    DoDAutonomyCollector(config),
    MBridgeCollector(config),
    JoblessClaimsCollector(config),      # NEW
    LuxuryCollapseCollector(config),     # NEW
    PharmacyShortageCollector(config),   # NEW
    SchoolClosureCollector(config)       # NEW
]
```

### 2. Update Dashboard

Edit `dashboard/app.py` to include new collectors:

```python
collectors = {
    'Treasury': TreasuryCollector(config),
    'ICEDetention': ICEDetentionCollector(config),
    'TaiwanZone': TaiwanZoneCollector(config),
    'HormuzRisk': HormuzRiskCollector(config),
    'DoDAutonomy': DoDAutonomyCollector(config),
    'MBridge': MBridgeCollector(config),
    'JoblessClaims': JoblessClaimsCollector(config),      # NEW
    'LuxuryCollapse': LuxuryCollapseCollector(config),    # NEW
    'PharmacyShortage': PharmacyShortageCollector(config), # NEW
    'SchoolClosures': SchoolClosureCollector(config)       # NEW
}
```

### 3. Update Dashboard JavaScript

Edit `dashboard/static/js/dashboard.js` to add friendly names and explanations:

```javascript
const friendlyNames = {
    // ... existing names ...
    'JoblessClaims': 'Unemployment Surge',
    'LuxuryCollapse': 'Rich People Fleeing',
    'PharmacyShortage': 'Medicine Shortages',
    'SchoolClosures': 'Schools Closing'
};

const descriptions = {
    // ... existing descriptions ...
    'JoblessClaims': 'Weekly unemployment filings - surge means layoffs spreading',
    'LuxuryCollapse': 'Rich selling luxury goods - they know something bad is coming',
    'PharmacyShortage': 'Critical medications unavailable at pharmacies',
    'SchoolClosures': 'Major school districts closed (not for weather)'
};

const whyItMatters = {
    // ... existing reasons ...
    'JoblessClaims': 'Mass layoffs → recession → mortgage crisis → bank failures',
    'LuxuryCollapse': 'Smart money fleeing → major crisis incoming → get ready',
    'PharmacyShortage': 'No meds → mental health crisis → social breakdown',
    'SchoolClosures': 'Parents cant work → economic disruption → cascade effects'
};
```

### 4. Adjust TIGHTEN-UP Threshold

With 10 indicators instead of 6, you might want to adjust when alerts trigger:

Edit `config/config.yaml`:
```yaml
alerts:
  tighten_up_threshold: 3  # Changed from 2 to 3 (30% in red)
```

### 5. Test the New Setup

```bash
# Test monitoring with new indicators
./venv/bin/python src/main.py --check-status

# View in dashboard
cd dashboard
./start_dashboard.sh
```

## Choosing Which Indicators to Add

From the new options, I recommend starting with:

1. **Jobless Claims** - Easy data, clear signal, updated weekly
2. **Pharmacy Shortage** - Critical for social stability, FDA provides data
3. **School Closures** - Immediate local impact, affects work/economy

The Luxury Collapse index is harder to implement (needs multiple data sources) but could be very valuable as an early warning.

## Data Source Setup

### For Jobless Claims:
- Get free API key from: https://fred.stlouisfed.org/docs/api/
- Add to `config/secrets.yaml`:
  ```yaml
  fred_api_key: "your_key_here"
  ```

### For Pharmacy Shortages:
- FDA RSS feed: https://www.fda.gov/drugs/drug-shortages/rss
- No API key needed

### For School Closures:
- Would need to aggregate from district websites
- Consider starting with just your local district

## Testing Tip

To test the new indicators trigger alerts, create a test config:

```yaml
# config/config_test_new_indicators.yaml
trip_wires:
  jobless_claims:
    thresholds:
      amber: 100  # Lowered from 275
      red: 200    # Lowered from 350
```

Then run: `python src/main.py --config config/config_test_new_indicators.yaml`