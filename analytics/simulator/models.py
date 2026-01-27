"""Data models for Digital Twin Simulator."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ScenarioType(Enum):
    """Types of actions that can be simulated."""
    ADD_CRA = "add_cra"
    REMOVE_CRA = "remove_cra"
    INCREASE_MONITORING = "increase_monitoring"
    DECREASE_MONITORING = "decrease_monitoring"
    CLOSE_SITE = "close_site"
    OPEN_SITE = "open_site"
    ADD_TRAINING = "add_training"
    EXTEND_TIMELINE = "extend_timeline"
    REALLOCATE_RESOURCES = "reallocate_resources"


@dataclass
class ScenarioAction:
    """A single action in a simulation scenario."""
    action_type: ScenarioType
    target: str  # e.g., "Region Europe" or "Site 456"
    value: float  # e.g., 2 for "add 2 CRAs" or 25 for "25% increase"
    
    def to_dict(self) -> Dict:
        return {
            "action_type": self.action_type.value,
            "target": self.target,
            "value": self.value
        }


@dataclass
class Scenario:
    """A complete simulation scenario with multiple actions."""
    name: str
    description: str
    actions: List[ScenarioAction]
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "actions": [a.to_dict() for a in self.actions]
        }


@dataclass
class MetricChange:
    """Represents a change in a specific metric."""
    metric_name: str
    baseline_value: float
    predicted_value: float
    change: float
    change_percent: float
    direction: str  # "improved", "declined", "unchanged"
    
    def to_dict(self) -> Dict:
        return {
            "metric_name": self.metric_name,
            "baseline_value": self.baseline_value,
            "predicted_value": self.predicted_value,
            "change": self.change,
            "change_percent": self.change_percent,
            "direction": self.direction
        }


@dataclass
class SimulationResult:
    """Results from running a simulation."""
    scenario_name: str
    scenario_description: str
    
    # Before vs After metrics
    baseline_dqi: float
    predicted_dqi: float
    dqi_change: float
    
    baseline_query_resolution_days: float
    predicted_query_resolution_days: float
    query_resolution_change: float
    
    baseline_timeline_risk: float
    predicted_timeline_risk: float
    timeline_risk_change: float
    
    # Cost/benefit
    estimated_cost_change: float
    roi_score: float  # Return on investment score
    
    # Confidence and details
    confidence_score: float
    metric_changes: List[MetricChange] = field(default_factory=list)
    site_level_predictions: Dict[str, Dict] = field(default_factory=dict)
    
    # LLM-generated content
    explanation: str = ""
    recommendations: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "scenario_name": self.scenario_name,
            "scenario_description": self.scenario_description,
            "baseline": {
                "dqi": self.baseline_dqi,
                "query_resolution_days": self.baseline_query_resolution_days,
                "timeline_risk": self.baseline_timeline_risk
            },
            "predicted": {
                "dqi": self.predicted_dqi,
                "query_resolution_days": self.predicted_query_resolution_days,
                "timeline_risk": self.predicted_timeline_risk
            },
            "changes": {
                "dqi_change": self.dqi_change,
                "query_resolution_change": self.query_resolution_change,
                "timeline_risk_change": self.timeline_risk_change,
                "cost_change": self.estimated_cost_change
            },
            "roi_score": self.roi_score,
            "confidence_score": self.confidence_score,
            "metric_changes": [m.to_dict() for m in self.metric_changes],
            "site_level_predictions": self.site_level_predictions,
            "explanation": self.explanation,
            "recommendations": self.recommendations,
            "risks": self.risks
        }


@dataclass
class ScenarioComparison:
    """Comparison of multiple scenarios."""
    scenarios: List[SimulationResult]
    best_for_dqi: str
    best_for_cost: str
    best_for_risk: str
    recommended_scenario: str
    recommendation_reason: str
    
    def to_dict(self) -> Dict:
        return {
            "scenarios": [s.to_dict() for s in self.scenarios],
            "best_for_dqi": self.best_for_dqi,
            "best_for_cost": self.best_for_cost,
            "best_for_risk": self.best_for_risk,
            "recommended_scenario": self.recommended_scenario,
            "recommendation_reason": self.recommendation_reason
        }
