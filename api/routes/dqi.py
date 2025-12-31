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
    from analytics.dqi import DQICalculator, StatisticalScorer
    
    # Use globally initialized calculator if available, mainly for caching
    from api.routes.dqi import get_analytics_calculator
    calculator = get_analytics_calculator()
    
    # Mock graph and explainer for now since legacy modules are missing
    return calculator, None, None


@router.get("/site/{site_id}", response_model=DQIResponse)
async def get_site_dqi(site_id: str, explain: bool = True):
    """Get DQI for a specific site."""
    try:
        calculator, explainer, graph = get_components()
        result = calculator.calculate_site(site_id)
        
        if explain:
             # Use LLM Validator for explanation
             from analytics.dqi import DQIValidator
             validator = DQIValidator()
             thresholds = calculator.rule_scorer.export_thresholds()
             
             # Use validation text as explanation
             result.explanation = validator.validate(result, thresholds)
             
             # Can also parse recommendations from validator output if structured, 
             # but for now rely on rule-based recommendations
             if not result.recommendations:
                 result.recommendations = ["Review validation summary for detailed actions."]
        
        return DQIResponse(
            entity_id=result.entity_id,
            entity_type=result.entity_type.value,
            score=result.score,
            grade=result.grade,
            status=result.status.value if hasattr(result.status, 'value') else str(result.status),
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
async def get_patient_dqi(patient_id: str, explain: bool = True):
    """Get DQI for a specific patient."""
    try:
        calculator, explainer, graph = get_components()
        result = calculator.calculate_patient(patient_id)
        
        if explain:
             # Use LLM Validator for explanation
             from analytics.dqi import DQIValidator
             validator = DQIValidator()
             thresholds = calculator.rule_scorer.export_thresholds()
             
             # Use validation text as explanation
             result.explanation = validator.validate(result, thresholds)
             
             # Can also parse recommendations from validator output if structured, 
             # but for now rely on rule-based recommendations
             if not result.recommendations:
                 result.recommendations = ["Review validation summary for detailed actions."]
        
        return DQIResponse(
            entity_id=result.entity_id,
            entity_type=result.entity_type.value,
            score=result.score,
            grade=result.grade,
            status=result.status.value if hasattr(result.status, 'value') else str(result.status),
            is_clean=result.is_clean,
            breakdown=[m.to_dict() if hasattr(m, 'to_dict') else {
                "metric": m.name,
                "value": m.raw_value,
                "contribution": m.contribution,
                "status": m.status.value if hasattr(m.status, 'value') else str(m.status)
            } for m in result.breakdown],
            explanation=result.explanation,
            recommendations=result.recommendations,
            top_issues=result.top_issues
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/study/{study_id}", response_model=DQIResponse)
async def get_study_dqi(study_id: str, explain: bool = True):
    """Get aggregated DQI for a study."""
    try:
        calculator, explainer, graph = get_components()
        result = calculator.calculate_study(study_id)
        
        if explain:
             # Use LLM Validator for explanation
             from analytics.dqi import DQIValidator
             validator = DQIValidator()
             thresholds = calculator.rule_scorer.export_thresholds()
             
             # Use validation text as explanation
             result.explanation = validator.validate(result, thresholds)
             
             # Can also parse recommendations from validator output if structured, 
             # but for now rely on rule-based recommendations
             if not result.recommendations:
                 result.recommendations = ["Review validation summary for detailed actions."]
        
        return DQIResponse(
            entity_id=result.entity_id,
            entity_type=result.entity_type.value,
            score=result.score,
            grade=result.grade,
            status=result.status.value if hasattr(result.status, 'value') else str(result.status),
            is_clean=result.is_clean,
            breakdown=[{
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


class ValidationRequest(BaseModel):
    entity_id: str
    entity_type: str = "site"


# Global instance of new calculator
_analytics_calculator = None


def get_analytics_calculator():
    global _analytics_calculator
    if _analytics_calculator is None:
        from analytics.dqi import DQICalculator, StatisticalScorer
        # Use empty stat scorer to avoid eager loading delay on first request
        _analytics_calculator = DQICalculator(stat_scorer=StatisticalScorer())
    return _analytics_calculator


@router.post("/validate")
async def validate_dqi(request: ValidationRequest):
    """
    Validate DQI result using LLM Insights.
    
    Uses rule-based validation to check for anomalies.
    """
    try:
        calc = get_analytics_calculator()
        
        # Calculate result first
        if request.entity_type.lower() == "site":
            result = calc.calculate_site(request.entity_id)
        elif request.entity_type.lower() == "patient":
            result = calc.calculate_patient(request.entity_id)
        elif request.entity_type.lower() == "study":
            result = calc.calculate_study(request.entity_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid entity type")
            
        # Run validation
        validation = calc.validate_result(result)
        
        return {
            "entity_id": result.entity_id,
            "score": result.score,
            "validation_summary": validation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
