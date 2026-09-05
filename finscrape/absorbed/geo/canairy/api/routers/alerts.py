"""
Alerts router
"""

from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()

@router.get("/")
async def get_alerts() -> List[Dict[str, Any]]:
    """Get all alerts"""
    return []

@router.post("/")
async def create_alert(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Create new alert"""
    return {"id": "1", **alert}