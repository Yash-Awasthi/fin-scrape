"""
Analytics router
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/hopi")
async def get_hopi_score() -> Dict[str, Any]:
    """Get HOPI score"""
    return {
        "total_score": 35.5,
        "threat_level": "amber",
        "phase": 2,
        "phase_name": "Elevated Monitoring"
    }

@router.get("/trends")
async def get_trends() -> Dict[str, Any]:
    """Get trend analysis"""
    return {
        "period": "last_7_days",
        "trends": []
    }