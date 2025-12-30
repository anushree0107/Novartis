"""DQI API - Data Quality Index endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()


class DQIResponse(BaseModel):
    entity_id: str
    entity_type: str
    score: float
    grade: str
    status: str
    is_clean: bool
    breakdown: List[Dict[str, Any]]
    explanation: Optional[str] = None
    recommendations: List[str] = []
    top_issues: List[str] = []


def get_components():
    from api.main import _dqi_calculator, _graph
    from intelligence.dqi import DQIExplainer
    if _dqi_calculator is None:
        raise HTTPException(status_code=500, detail="DQI not initialized")
    return _dqi_calculator, DQIExplainer(), _graph


@router.get("/site/{site_id}", response_model=DQIResponse)
async def get_site_dqi(site_id: str, explain: bool = True):
    """Get DQI for a specific site."""
    try:
        calculator, explainer, graph = get_components()
        result = calculator.calculate_site(site_id)
        
        if explain:
            result.explanation = explainer.explain(result)
            result.recommendations = explainer.generate_recommendations(result)
        
        return DQIResponse(
            entity_id=result.entity_id,
            entity_type=result.entity_type.value,
            score=result.score,
            grade=result.grade,
            status=result.status,
            is_clean=result.is_clean,
            breakdown=[m.to_dict() if hasattr(m, 'to_dict') else {
                "metric": m.name,
                "value": m.raw_value,
                "contribution": m.contribution,
                "status": m.status
            } for m in result.breakdown],
            explanation=result.explanation,
            recommendations=result.recommendations,
            top_issues=result.top_issues
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patient/{patient_id}", response_model=DQIResponse)
async def get_patient_dqi(patient_id: str):
    """Get DQI for a specific patient."""
    try:
        calculator, explainer, graph = get_components()
        result = calculator.calculate_patient(patient_id)
        
        return DQIResponse(
            entity_id=result.entity_id,
            entity_type=result.entity_type.value,
            score=result.score,
            grade=result.grade,
            status=result.status,
            is_clean=result.is_clean,
            breakdown=[{
                "metric": m.name,
                "value": m.raw_value,
                "contribution": m.contribution,
                "status": m.status
            } for m in result.breakdown],
            top_issues=result.top_issues
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/study/{study_id}", response_model=DQIResponse)
async def get_study_dqi(study_id: str):
    """Get aggregated DQI for a study."""
    try:
        calculator, explainer, graph = get_components()
        result = calculator.calculate_study(study_id)
        
        return DQIResponse(
            entity_id=result.entity_id,
            entity_type=result.entity_type.value,
            score=result.score,
            grade=result.grade,
            status=result.status,
            is_clean=result.is_clean,
            breakdown=[{
                "metric": m.name,
                "value": m.raw_value,
                "contribution": m.contribution,
                "status": m.status
            } for m in result.breakdown],
            top_issues=result.top_issues
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
