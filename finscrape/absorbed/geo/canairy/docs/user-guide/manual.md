# Canairy User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Understanding the Dashboard](#understanding-the-dashboard)
4. [Interpreting Indicators](#interpreting-indicators)
5. [Alert System](#alert-system)
6. [Taking Action](#taking-action)
7. [News Intelligence](#news-intelligence)
8. [Customization](#customization)
9. [Mobile Usage](#mobile-usage)
10. [Troubleshooting](#troubleshooting)

## Introduction

Welcome to Canairy - your personal early warning system for global disruptions. This manual will help you understand how to use Canairy effectively to protect your family and prepare for potential challenges.

### What Canairy Does

Canairy monitors 22 critical indicators across four major categories:
- **Financial** - Banking stress, market volatility, currency risks
- **Supply Chain** - Product shortages, shipping disruptions, trade conflicts
- **Energy** - Power grid stability, fuel prices, infrastructure risks
- **Social** - Civil unrest, immigration enforcement, geopolitical tensions

## Getting Started

### First Time Setup

1. **Access the Dashboard**
   - Open your browser and navigate to http://localhost:3005
   - You'll see the main dashboard with current system status

2. **Configure API Keys** (Optional but Recommended)
   - Click Settings (gear icon) in the sidebar
   - Enter your API keys for enhanced features:
     - News API - Real-time news filtering
     - Alpha Vantage - Market data
     - OpenAI - Advanced news analysis

3. **Set Your Location** (Important!)
   - Go to Settings → Location
   - Enter your city or zip code
   - This helps prioritize local risks and relevant news

4. **Configure Notifications**
   - Settings → Notifications
   - Choose your alert preferences:
     - Email alerts
     - Browser notifications
     - SMS (premium feature)
   - Set quiet hours if desired

### Understanding System Status

The top status bar shows four key metrics:

```
[🟢 NORMAL] | Phase 0 Active | HOPI: 23.5 ↓ | Time to Act: Days
```

- **Threat Level**: 🟢 Normal, 🟡 Elevated, 🟠 High, 🔴 Critical
- **Current Phase**: 0-3 escalation system
- **HOPI Score**: Overall risk score (0-100)
- **Time to Act**: Urgency indicator

## Understanding the Dashboard

### Main Dashboard Components

#### 1. Executive Summary
The large panel at the top provides a natural language summary of the current situation:
- Main threat assessment
- Confidence level
- Key risks identified
- Expected impact timeline

#### 2. Critical Indicators Panel
Shows the top 5 most concerning indicators:
- Red indicators (immediate concern)
- Amber indicators (elevated risk)
- Each shows current value, trend, and impact

#### 3. Risk Narrative
Provides historical context:
- Pattern matching with past events
- Similarity scores
- Expected outcomes based on history

#### 4. Priority Actions
Your personalized action checklist:
- Immediate actions (red - do now)
- Today actions (amber - within 24 hours)
- This week actions (blue - preparatory)

### Reading Indicator Cards

Each indicator card displays:

```
┌─────────────────────────────┐
│ Treasury Tail Risk    🔴 2.8 │
│ ▂▃▅▆█▆▅▃▂ (24h chart)      │
│ Banking stress critical     │
│ Updated: 5 minutes ago      │
└─────────────────────────────┘
```

- **Name**: What's being monitored
- **Status Light**: 🟢 Green, 🟡 Amber, 🔴 Red
- **Current Value**: Latest measurement
- **Mini Chart**: 24-hour trend
- **Impact**: Plain English explanation
- **Freshness**: When last updated

### Chart Types

Different indicators use different visualizations:
- **Gauge**: For percentage-based metrics (ICE detention capacity)
- **Area Chart**: For continuous values (VIX volatility)
- **Bar Chart**: For discrete measurements (unemployment rate)
- **Binary**: For on/off states (Taiwan exclusion zone)

## Interpreting Indicators

### Color Coding System

#### 🟢 Green (Normal)
- No immediate concern
- Continue normal activities
- Maintain basic preparedness

#### 🟡 Amber (Elevated)
- Increased monitoring needed
- Review preparedness supplies
- Stay informed on developments

#### 🔴 Red (Critical)
- Immediate action recommended
- Follow priority action checklist
- Prepare for potential impacts

### Understanding Thresholds

Each indicator has specific thresholds:

**Example: Treasury Tail Risk**
- Green: < 1.5 (Normal market function)
- Amber: 1.5 - 2.5 (Stress building)
- Red: > 2.5 (Banking system at risk)

Click any indicator for detailed threshold explanations.

## Alert System

### Alert Types

1. **Status Change Alerts**
   - Indicator moves between color zones
   - Phase transitions
   - New critical indicators

2. **Trend Alerts**
   - Rapid deterioration detected
   - Multiple indicators moving together
   - Pattern matching historical crises

3. **Action Reminders**
   - Uncompleted priority actions
   - Time-sensitive preparations
   - Follow-up on previous alerts

### Managing Alerts

- **Acknowledge**: Click ✓ to mark as read
- **Snooze**: Delay reminder for 1, 4, or 24 hours
- **Details**: View full context and recommendations
- **History**: Access Settings → Alert History

## Taking Action

### Priority Actions Explained

Each action includes:
- **Why**: The specific risk you're protecting against
- **Steps**: Numbered checklist of what to do
- **Resources**: Phone numbers, links, checklists
- **Time Required**: Realistic time estimate
- **Impact**: What this protects

### Action Categories

#### 🏦 Financial Actions
- Secure bank deposits
- Diversify holdings
- Increase cash reserves
- Document account access

#### 🛒 Supply Chain Actions
- Stock essential supplies
- Fuel vehicles
- Refill prescriptions
- Purchase shelf-stable food

#### ⚡ Energy Actions
- Test backup power
- Charge devices
- Fill propane tanks
- Prepare for outages

#### 👨‍👩‍👧‍👦 Family Actions
- Update emergency contacts
- Establish meeting points
- Pack go-bags
- Practice evacuation routes

### Completing Actions

1. Click the checkbox next to each completed step
2. Use resource buttons for quick access:
   - 📞 Phone numbers dial directly
   - 🔗 Links open in new tab
   - 📋 Checklists copy to clipboard
3. Track completion percentage at top

## News Intelligence

### News Sidebar

Toggle with the 📰 button in the header:
- Filtered by active risk indicators
- Credibility scores for sources
- Related indicators highlighted
- Auto-refreshes every 5 minutes

### News Item Features

Each news item shows:
- **Headline** with source credibility
- **Time**: How recent (critical if < 1 hour)
- **Related Indicators**: Color-coded badges
- **Expand**: Click for full summary

### News Ticker

The scrolling ticker shows:
- Breaking news related to risks
- Only high-credibility sources
- Click any item for details

## Customization

### Dashboard Settings

**Display Options**
- Indicator sort order
- Chart time ranges
- News feed preferences
- Language selection

**Data Management**
- Export historical data
- Clear cache
- Reset to defaults
- Backup settings

### Indicator Preferences

For each indicator, you can:
- Adjust threshold sensitivity
- Enable/disable specific alerts
- Set custom notes
- Choose data sources

## Mobile Usage

### Progressive Web App

Install Canairy on your phone:
1. Open in mobile browser
2. Click "Add to Home Screen"
3. Accept installation prompt
4. Access like native app

### Mobile Features
- Swipe between dashboard sections
- Touch-friendly action buttons
- Optimized data usage
- Offline mode for viewing

### Mobile Tips
- Enable push notifications
- Use landscape for charts
- Set mobile-specific quiet hours
- Configure location services

## Troubleshooting

### Common Issues

#### "No Data" on Indicators
- Check internet connection
- Verify API keys in settings
- Look for service status updates
- Try manual refresh (↻ button)

#### Alerts Not Working
- Check notification permissions
- Verify email in settings
- Test with Settings → Send Test Alert
- Check spam folder

#### Slow Performance
- Clear browser cache
- Disable unused news sources
- Reduce chart history range
- Close other browser tabs

### Data Accuracy

**How We Ensure Accuracy**
- Multiple data sources per indicator
- Automatic fallback systems
- Data validation checks
- Manual override options

**Reporting Issues**
- Click indicator → Report Issue
- Include screenshot if possible
- Describe expected vs actual
- Check GitHub issues

### Getting Help

**Resources**
- This manual: `/docs/user-guide/manual.md`
- Video tutorials: YouTube channel
- Community: GitHub Discussions
- Emergency: support@canairy.app

**Debug Information**
Access Settings → System Info for:
- Version numbers
- Connection status
- Error logs
- Performance metrics

## Best Practices

### Daily Routine
1. **Morning Check** (2 minutes)
   - Review overnight changes
   - Check priority actions
   - Scan news highlights

2. **Evening Review** (5 minutes)
   - Complete any urgent actions
   - Update completed tasks
   - Plan for tomorrow

### Weekly Maintenance
- Review and update emergency contacts
- Test one backup system
- Check supply expiration dates
- Update family on any changes

### Monthly Tasks
- Full system test
- Review historical trends
- Update location settings
- Export data backup

## Emergency Procedures

### When Multiple Indicators Turn Red

1. **Don't Panic** - You have time to act
2. **Check Priority Actions** - Follow the checklist
3. **Inform Family** - Share dashboard link
4. **Execute Plan** - Work through actions methodically
5. **Stay Informed** - Monitor news sidebar

### Phase Transitions

**Phase 0 → 1**: Heightened Awareness
- Review all preparedness supplies
- Ensure all contacts updated
- Top off fuel and supplies

**Phase 1 → 2**: Active Preparation
- Execute all amber actions
- Coordinate with family
- Prepare to shelter in place

**Phase 2 → 3**: Crisis Response
- Complete all red actions immediately
- Activate family emergency plan
- Monitor official emergency channels

## Conclusion

Canairy is your partner in family preparedness. By understanding these features and following the guidance provided, you can:
- Stay ahead of disruptions
- Protect your family's resources
- Make informed decisions
- Maintain peace of mind

Remember: **Early warning enables early action**. The goal isn't to live in fear, but to live prepared.

---

*For technical support or questions not covered in this manual, please visit our [GitHub repository](https://github.com/manavpthaker/canairy) or email support@canairy.app*