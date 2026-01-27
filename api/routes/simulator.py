"""API routes for Digital Twin Simulator."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from analytics.simulator import (
    DigitalTwinSimulator,
    Scenario,
    ScenarioAction,
    ScenarioType
)

router = APIRouter(tags=["Digital Twin Simulator"])

# Pydantic models for request/response
class ActionRequest(BaseModel):
    """Single action in a simulation scenario."""
    action_type: str = Field(..., description="Type of action: add_cra, remove_cra, increase_monitoring, etc.")
    target: str = Field(..., description="Target of action: region name, site ID, or 'All Sites'")
    value: float = Field(..., description="Value for the action: count for CRAs, percentage for monitoring, etc.")


class ScenarioRequest(BaseModel):
    """Request to run a simulation scenario."""
    name: str = Field(..., description="Name of the scenario")
    description: str = Field("", description="Description of what the scenario tests")
    actions: List[ActionRequest] = Field(..., description="List of actions to simulate")


class CompareRequest(BaseModel):
    """Request to compare multiple scenarios."""
    scenarios: List[ScenarioRequest] = Field(..., description="List of scenarios to compare")


class MetricChangeResponse(BaseModel):
    """Response for a single metric change."""
    metric_name: str
    baseline_value: float
    predicted_value: float
    change: float
    change_percent: float
    direction: str


class SimulationResponse(BaseModel):
    """Response from running a simulation."""
    success: bool
    scenario_name: str
    baseline: Dict[str, float]
    predicted: Dict[str, float]
    changes: Dict[str, float]
    roi_score: float
    confidence_score: float
    explanation: str
    recommendations: List[str]
    risks: List[str]
    metric_changes: List[Dict[str, Any]]


class ComparisonResponse(BaseModel):
    """Response from comparing scenarios."""
    success: bool
    scenarios: List[Dict[str, Any]]
    best_for_dqi: str
    best_for_cost: str
    best_for_risk: str
    recommended_scenario: str
    recommendation_reason: str


# Initialize simulator (will be recreated per request with fresh data)
def get_simulator() -> DigitalTwinSimulator:
    """Get a fresh simulator instance."""
    return DigitalTwinSimulator(data_dir="processed_data")


def parse_action(action_req: ActionRequest) -> ScenarioAction:
    """Parse action request into ScenarioAction."""
    try:
        action_type = ScenarioType(action_req.action_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action type: {action_req.action_type}. Valid types: {[t.value for t in ScenarioType]}"
        )
    return ScenarioAction(
        action_type=action_type,
        target=action_req.target,
        value=action_req.value
    )


@router.post("/run", response_model=SimulationResponse)
async def run_simulation(request: ScenarioRequest):
    """
    Run a single simulation scenario.
    
    This endpoint simulates "what-if" scenarios for clinical trial optimization.
    
    Example:
    ```json
    {
        "name": "Add CRA Support",
        "description": "Test adding CRAs to Europe",
        "actions": [
            {"action_type": "add_cra", "target": "Region Europe", "value": 2}
        ]
    }
    ```
    """
    try:
        # Parse actions
        actions = [parse_action(a) for a in request.actions]
        
        # Create scenario
        scenario = Scenario(
            name=request.name,
            description=request.description,
            actions=actions
        )
        
        # Run simulation
        simulator = get_simulator()
        result = simulator.run_simulation(scenario)
        
        return SimulationResponse(
            success=True,
            scenario_name=result.scenario_name,
            baseline={
                "dqi": result.baseline_dqi,
                "query_resolution_days": result.baseline_query_resolution_days,
                "timeline_risk": result.baseline_timeline_risk
            },
            predicted={
                "dqi": result.predicted_dqi,
                "query_resolution_days": result.predicted_query_resolution_days,
                "timeline_risk": result.predicted_timeline_risk
            },
            changes={
                "dqi_change": result.dqi_change,
                "query_resolution_change": result.query_resolution_change,
                "timeline_risk_change": result.timeline_risk_change,
                "cost_change": result.estimated_cost_change
            },
            roi_score=result.roi_score,
            confidence_score=result.confidence_score,
            explanation=result.explanation,
            recommendations=result.recommendations,
            risks=result.risks,
            metric_changes=[m.to_dict() for m in result.metric_changes]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")


@router.post("/compare", response_model=ComparisonResponse)
async def compare_scenarios(request: CompareRequest):
    """
    Compare multiple simulation scenarios side-by-side.
    
    This helps identify the best approach by comparing DQI improvements,
    costs, and risks across different scenarios.
    """
    try:
        scenarios = []
        for s in request.scenarios:
            actions = [parse_action(a) for a in s.actions]
            scenarios.append(Scenario(
                name=s.name,
                description=s.description,
                actions=actions
            ))
        
        simulator = get_simulator()
        comparison = simulator.compare_scenarios(scenarios)
        
        return ComparisonResponse(
            success=True,
            scenarios=[s.to_dict() for s in comparison.scenarios],
            best_for_dqi=comparison.best_for_dqi,
            best_for_cost=comparison.best_for_cost,
            best_for_risk=comparison.best_for_risk,
            recommended_scenario=comparison.recommended_scenario,
            recommendation_reason=comparison.recommendation_reason
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.get("/presets")
async def get_preset_scenarios():
    """
    Get common preset scenarios for quick testing.
    
    These are pre-configured scenarios that represent common
    optimization strategies for clinical trials.
    """
    simulator = get_simulator()
    presets = simulator.get_preset_scenarios()
    
    return {
        "presets": [
            {
                "name": p.name,
                "description": p.description,
                "actions": [a.to_dict() for a in p.actions]
            }
            for p in presets
        ]
    }


@router.get("/regions")
async def get_available_regions():
    """Get list of available regions for simulation."""
    simulator = get_simulator()
    return {"regions": simulator.get_available_regions()}


@router.get("/sites")
async def get_available_sites():
    """Get list of available sites for simulation."""
    simulator = get_simulator()
    return {"sites": simulator.get_available_sites()}


@router.get("/action-types")
async def get_action_types():
    """Get list of available action types with descriptions."""
    return {
        "action_types": [
            {
                "type": "add_cra",
                "name": "Add CRA",
                "description": "Add Clinical Research Associates to a region",
                "value_description": "Number of CRAs to add"
            },
            {
                "type": "remove_cra",
                "name": "Remove CRA",
                "description": "Remove CRAs from a region",
                "value_description": "Number of CRAs to remove"
            },
            {
                "type": "increase_monitoring",
                "name": "Increase Monitoring",
                "description": "Increase monitoring frequency",
                "value_description": "Percentage increase (e.g., 25 for 25%)"
            },
            {
                "type": "decrease_monitoring",
                "name": "Decrease Monitoring",
                "description": "Decrease monitoring frequency",
                "value_description": "Percentage decrease"
            },
            {
                "type": "close_site",
                "name": "Close Site",
                "description": "Close an underperforming site",
                "value_description": "Set to 1 to close"
            },
            {
                "type": "add_training",
                "name": "Add Training",
                "description": "Add training sessions for staff",
                "value_description": "Number of training sessions"
            },
            {
                "type": "extend_timeline",
                "name": "Extend Timeline",
                "description": "Extend trial timeline",
                "value_description": "Number of weeks to extend"
            }
        ]
    }


@router.get("/baseline")
async def get_baseline_metrics():
    """Get current baseline metrics for the trial."""
    simulator = get_simulator()
    baseline = simulator.get_baseline_metrics()
    
    return {
        "baseline": baseline,
        "trial_info": {
            "total_sites": simulator.trial_data.get("total_sites", 0),
            "total_patients": simulator.trial_data.get("total_patients", 0),
            "total_open_queries": simulator.trial_data.get("total_open_queries", 0),
            "regions": len(simulator.region_data)
        }
    }
