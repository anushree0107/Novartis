"""Alerts API - Proactive alerting endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()


class AlertResponse(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    category: str
    entity_type: str
    entity_id: str
    recommended_action: str = ""
    llm_analysis: str = ""


class AlertSummary(BaseModel):
    total_alerts: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]
    top_alerts: List[Dict[str, Any]]


def get_alert_engine():
    from api.main import _alert_engine
    if _alert_engine is None:
        raise HTTPException(status_code=500, detail="AlertEngine not initialized")
    return _alert_engine


@router.get("/", response_model=List[AlertResponse])
async def get_all_alerts(limit: int = 50):
    """Get all active alerts."""
    try:
        engine = get_alert_engine()
        alerts = engine.scan_all()[:limit]
        
        return [
            AlertResponse(
                id=a.id,
                title=a.title,
                description=a.description,
                severity=a.severity.value,
                category=a.category.value,
                entity_type=a.entity_type,
                entity_id=a.entity_id,
                recommended_action=a.recommended_action,
                llm_analysis=a.llm_analysis
            )
            for a in alerts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=AlertSummary)
async def get_alert_summary():
    """Get alert summary statistics."""
    try:
        engine = get_alert_engine()
        summary = engine.get_summary()
        
        return AlertSummary(
            total_alerts=summary["total_alerts"],
            by_severity=summary["by_severity"],
            by_category=summary["by_category"],
            top_alerts=summary["top_alerts"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/site/{site_id}", response_model=List[AlertResponse])
async def get_site_alerts(site_id: str):
    """Get alerts for a specific site."""
    try:
        engine = get_alert_engine()
        alerts = engine.get_alerts_for_entity("site", site_id)
        
        return [
            AlertResponse(
                id=a.id,
                title=a.title,
                description=a.description,
                severity=a.severity.value,
                category=a.category.value,
                entity_type=a.entity_type,
                entity_id=a.entity_id,
                recommended_action=a.recommended_action
            )
            for a in alerts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/severity/{severity}", response_model=List[AlertResponse])
async def get_alerts_by_severity(severity: str):
    """Get alerts by severity level."""
    try:
        engine = get_alert_engine()
        from alerting import AlertSeverity
        
        severity_enum = None
        for s in AlertSeverity:
            if s.value == severity.lower():
                severity_enum = s
                break
        
        if not severity_enum:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
        
        alerts = engine.get_alerts_by_severity(severity_enum)
        
        return [
            AlertResponse(
                id=a.id,
                title=a.title,
                description=a.description,
                severity=a.severity.value,
                category=a.category.value,
                entity_type=a.entity_type,
                entity_id=a.entity_id,
                recommended_action=a.recommended_action
            )
            for a in alerts
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
