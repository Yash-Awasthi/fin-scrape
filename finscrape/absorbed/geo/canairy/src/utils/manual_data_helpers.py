"""
Helper functions for manual data entry files.
Creates template files for manual trip-wire data entry.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

def create_manual_data_templates():
    """Create template files for manual data entry."""
    logger = logging.getLogger("manual_data_helpers")
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    templates = {
        "ice_detention_manual.json": {
            "description": "ICE detention bed fill rate data",
            "source": "DHS ICE Detention Statistics weekly PDF",
            "latest": {
                "beds_used": 45000,
                "total_beds": 50000,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "Update weekly from DHS reports"
            },
            "instructions": "Update 'latest' section with current data from DHS PDFs"
        },
        
        "taiwan_status_manual.json": {
            "description": "Taiwan exclusion zone status",
            "source": "CSIS Taiwan updates, Reuters, defense news",
            "current_status": "NONE",
            "valid_statuses": ["NONE", "TEMP", "BLOCKADE"],
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "instructions": "Update 'current_status' based on credible defense news"
        },
        
        "hormuz_wri_manual.json": {
            "description": "Hormuz war risk insurance premium",
            "source": "Lloyd's List, S&P Platts, maritime insurance reports",
            "latest_wri_percent": 0.5,
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Percentage of cargo value for war risk insurance",
            "instructions": "Update with latest WRI quotes from maritime sources"
        },
        
        "dod_autonomy_manual.json": {
            "description": "DoD autonomous weapons policy status",
            "source": "SAM.gov solicitations, defense policy documents",
            "current_policy": "HUMAN VETO",
            "valid_policies": ["HUMAN VETO", "PILOT", "REMOVED"],
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "instructions": "Update based on DoD solicitation language analysis"
        },
        
        "mbridge_settlement_manual.json": {
            "description": "mBridge gulf crude settlement share",
            "source": "BIS Project mBridge reports, IMF working papers",
            "latest_share_percent": 0.1,
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Percentage of gulf crude trades settled via mBridge",
            "instructions": "Update from BIS/IMF official publications"
        }
    }
    
    for filename, template in templates.items():
        filepath = raw_dir / filename
        
        if not filepath.exists():
            with open(filepath, 'w') as f:
                json.dump(template, f, indent=2)
            logger.info(f"Created template: {filepath}")
        else:
            logger.debug(f"Template already exists: {filepath}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_manual_data_templates()
    print("Manual data templates created in data/raw/")