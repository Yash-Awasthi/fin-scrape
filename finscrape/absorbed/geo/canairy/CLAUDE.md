# Household Resilience Trip-Wire Monitoring System

This is an AI-driven household resilience monitoring system based on the "Risk and Household Resilience" analysis document. It automates the tracking of 6 critical societal risk indicators and provides family-level preparedness alerts.

## Project Overview

**Purpose**: Automate monitoring of AI-driven societal risks (H1-H6) and translate them into actionable household preparedness phases (0-9).

**Core Function**: Track trip-wire metrics, assess threat levels (green/amber/red), and trigger "TIGHTEN-UP" protocols when ≥2 metrics hit red status.

## Tech Stack

- **Language**: Python 3.11+
- **Dependencies**: requests, pyyaml, schedule, pandas, matplotlib, smtplib
- **Data Storage**: JSON files + CSV exports
- **Configuration**: YAML-based
- **Notifications**: Email, SMS (Twilio), desktop alerts
- **Visualization**: matplotlib + HTML dashboard

## Architecture

```
src/
├── collectors/     # Data fetching modules for each trip-wire
├── processors/     # Threshold analysis and alert logic
├── notifications/  # Email, SMS, desktop notification handlers
└── utils/         # Helper functions and common utilities
```

## Commands

```bash
# Setup and Installation
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Development
python src/main.py          # Run monitoring system
python src/test_runner.py   # Run all tests
python scripts/setup.py     # Initial configuration wizard

# Maintenance
python scripts/backup.py         # Backup historical data
python scripts/validate_config.py # Check configuration
python scripts/update_sources.py  # Update data source URLs

# Dashboard
python dashboard/serve.py    # Launch web dashboard (localhost:8080)
```

## Trip-Wire Metrics (H1-H6)

1. **Treasury Tail** (H1): 10-yr auction tail basis points
2. **ICE Detention** (H4): Detention bed fill percentage  
3. **Taiwan Zone** (H2): PLA exclusion zone status
4. **Hormuz Risk** (H2): War risk insurance premium
5. **DoD Autonomy** (H2): Auto-execute policy status
6. **mBridge** (H1): Gulf crude settlement share

## Configuration

- Main config: `config/config.yaml`
- Secrets: `config/secrets.yaml` (git-ignored)
- Trip-wire thresholds: `config/thresholds.yaml`

## Data Sources

- **Automated**: Treasury API, RSS feeds, web scraping
- **Manual**: ICE detention reports (PDF), DoD solicitations
- **Hybrid**: Social media monitoring for Taiwan/Hormuz alerts

## Code Style

- Use type hints for all functions
- Follow PEP 8 formatting
- Prefer f-strings over .format()
- Use dataclasses for structured data
- Error handling: try/except with logging
- Async for I/O operations where beneficial

## Important Notes

- This system monitors **public information only**
- All data sources are legitimate government/financial APIs
- Alert thresholds based on documented research (see docs/research.md)
- Privacy-first: no personal data collection beyond email/SMS for alerts

## Testing

- Unit tests for each collector module
- Integration tests for alert workflows  
- Mock data for threshold testing
- CI/CD via GitHub Actions (if hosted)

## Git Workflow

- Main branch for production-ready code
- Feature branches for new collectors/processors
- Commit messages: `feat/fix/docs: description`
- Always run tests before committing

## Security

- Secrets stored in environment variables
- API keys in git-ignored files only
- Input validation on all external data
- Rate limiting for API calls

## Deployment

- Development: Local Python environment
- Production: Could be containerized or run on home server
- Backup: Daily exports to cloud storage (encrypted)

## Documentation

- Trip-wire formulas: `docs/trip-wire-formulas.md`
- Phase actions: `docs/phase-actions.md`
- API documentation: `docs/api.md`
- Setup guide: `docs/setup.md`
