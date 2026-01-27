"""Digital Twin Simulation Engine.

Main engine that runs "what-if" scenarios for clinical trial optimization.
Integrates with existing DQI and data infrastructure.
"""

import os
import logging
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

from .models import (
    ScenarioType,
    ScenarioAction,
    Scenario,
    SimulationResult,
    MetricChange,
    ScenarioComparison
)
from .impact_models import ImpactModel, ImpactCoefficients

logger = logging.getLogger("digital_twin")


class DigitalTwinSimulator:
    """
    Main simulation engine for clinical trial "what-if" analysis.
    
    This creates a virtual copy of the trial where different scenarios
    can be tested without affecting real data.
    """
    
    def __init__(
        self,
        data_dir: str = "processed_data",
        llm=None,
        coefficients: ImpactCoefficients = None
    ):
        """
        Initialize the Digital Twin Simulator.
        
        Args:
            data_dir: Directory containing processed trial data
            llm: Optional LLM for generating explanations
            coefficients: Custom impact coefficients (uses defaults if None)
        """
        self.data_dir = Path(data_dir)
        self.llm = llm
        self.impact_model = ImpactModel(coefficients)
        
        # Load trial data
        self._load_trial_data()
        
        # Cache for computed baselines
        self._baseline_cache: Dict[str, Any] = {}
        
    def _load_trial_data(self):
        """Load all relevant trial data for simulation."""
        self.trial_data = {}
        self.site_data = {}
        self.region_data = {}
        
        try:
            # Load site-level data
            site_path = self.data_dir / "site_master_processed_df.csv"
            if site_path.exists():
                self.sites_df = pd.read_csv(site_path)
                self._process_site_data()
            else:
                self.sites_df = pd.DataFrame()
                logger.warning(f"Site data not found at {site_path}")
                
            # Load study-level data
            study_path = self.data_dir / "study_master_processed_df.csv"
            if study_path.exists():
                self.studies_df = pd.read_csv(study_path)
            else:
                self.studies_df = pd.DataFrame()
                
            # Load query metrics
            query_path = self.data_dir / "query_open_processed_df.csv"
            if query_path.exists():
                self.queries_df = pd.read_csv(query_path)
            else:
                self.queries_df = pd.DataFrame()
                
            # Load missing pages data
            missing_path = self.data_dir / "missing_pages_processed_df.csv"
            if missing_path.exists():
                self.missing_df = pd.read_csv(missing_path)
            else:
                self.missing_df = pd.DataFrame()
                
            # Compute aggregate trial metrics
            self._compute_trial_metrics()
            
        except Exception as e:
            logger.error(f"Error loading trial data: {e}")
            self._set_default_data()
            
    def _process_site_data(self):
        """Process site data into lookup dictionaries."""
        if self.sites_df.empty:
            return
            
        for _, row in self.sites_df.iterrows():
            site_id = row.get("site", f"Site_{row.name}")
            self.site_data[site_id] = {
                "site_id": site_id,
                "study_id": row.get("study_id", "Unknown"),
                "country": row.get("country", "Unknown"),
                "region": row.get("region", "Unknown"),
                "patient_count": row.get("subject_count", 0),
                "dqi": row.get("dqi_score", 70),
                "open_queries": row.get("open_queries", 0),
                "operational_cost": 50000  # Default estimate
            }
            
            # Aggregate by region
            region = row.get("region", "Unknown")
            if region not in self.region_data:
                self.region_data[region] = {
                    "region": region,
                    "sites_count": 0,
                    "total_patients": 0,
                    "avg_dqi": 0,
                    "cra_count": 5,  # Default estimate
                    "dqi_sum": 0
                }
            self.region_data[region]["sites_count"] += 1
            self.region_data[region]["total_patients"] += row.get("subject_count", 0)
            self.region_data[region]["dqi_sum"] += row.get("dqi_score", 70)
            
        # Calculate average DQI per region
        for region in self.region_data:
            sites_count = self.region_data[region]["sites_count"]
            if sites_count > 0:
                self.region_data[region]["avg_dqi"] = (
                    self.region_data[region]["dqi_sum"] / sites_count
                )
                
    def _compute_trial_metrics(self):
        """Compute aggregate trial-level metrics."""
        self.trial_data = {
            "total_sites": len(self.site_data),
            "total_patients": sum(s.get("patient_count", 0) for s in self.site_data.values()),
            "avg_dqi": 70,  # Default
            "avg_query_resolution_days": 7,  # Default
            "timeline_risk_percent": 15,  # Default
            "total_open_queries": 0,
            "monitoring_frequency": 100  # Baseline = 100%
        }
        
        # Calculate actual average DQI
        if self.site_data:
            dqi_values = [s.get("dqi", 70) for s in self.site_data.values()]
            self.trial_data["avg_dqi"] = np.mean(dqi_values)
            
        # Calculate open queries
        if not self.queries_df.empty and "site" in self.queries_df.columns:
            self.trial_data["total_open_queries"] = len(self.queries_df)
            
        # Estimate timeline risk based on data quality
        avg_dqi = self.trial_data["avg_dqi"]
        if avg_dqi >= 85:
            self.trial_data["timeline_risk_percent"] = 5
        elif avg_dqi >= 70:
            self.trial_data["timeline_risk_percent"] = 15
        elif avg_dqi >= 55:
            self.trial_data["timeline_risk_percent"] = 30
        else:
            self.trial_data["timeline_risk_percent"] = 50
            
    def _set_default_data(self):
        """Set default data when actual data is unavailable."""
        self.sites_df = pd.DataFrame()
        self.studies_df = pd.DataFrame()
        self.queries_df = pd.DataFrame()
        self.missing_df = pd.DataFrame()
        
        # Default trial metrics for demo
        self.trial_data = {
            "total_sites": 25,
            "total_patients": 500,
            "avg_dqi": 72,
            "avg_query_resolution_days": 8,
            "timeline_risk_percent": 18,
            "total_open_queries": 150,
            "monitoring_frequency": 100
        }
        
        # Default regions for demo
        self.region_data = {
            "Region Europe": {"region": "Region Europe", "sites_count": 8, "cra_count": 4, "avg_dqi": 68, "total_patients": 180},
            "Region North America": {"region": "Region North America", "sites_count": 10, "cra_count": 6, "avg_dqi": 76, "total_patients": 200},
            "Region Asia Pacific": {"region": "Region Asia Pacific", "sites_count": 7, "cra_count": 3, "avg_dqi": 71, "total_patients": 120}
        }
        
        # Default sites for demo
        self.site_data = {}
        for i in range(1, 26):
            self.site_data[f"Site {i}"] = {
                "site_id": f"Site {i}",
                "patient_count": np.random.randint(10, 40),
                "dqi": np.random.randint(50, 95),
                "open_queries": np.random.randint(0, 20),
                "operational_cost": 50000
            }
            
    def get_baseline_metrics(self) -> Dict[str, float]:
        """Get current trial metrics as baseline for comparison."""
        return {
            "avg_dqi": self.trial_data.get("avg_dqi", 70),
            "avg_query_resolution_days": self.trial_data.get("avg_query_resolution_days", 7),
            "timeline_risk_percent": self.trial_data.get("timeline_risk_percent", 15),
            "total_cost": self._estimate_current_costs()
        }
        
    def _estimate_current_costs(self) -> float:
        """Estimate current operational costs."""
        # Rough estimation based on sites and patients
        site_cost = len(self.site_data) * 50000  # $50k per site
        cra_cost = sum(r.get("cra_count", 5) for r in self.region_data.values()) * 85000
        return site_cost + cra_cost
        
    def run_simulation(self, scenario: Scenario) -> SimulationResult:
        """
        Run a simulation scenario and predict outcomes.
        
        Args:
            scenario: The scenario to simulate
            
        Returns:
            SimulationResult with predicted metrics and explanations
        """
        # Get baseline
        baseline = self.get_baseline_metrics()
        
        # Track cumulative changes
        total_dqi_change = 0.0
        total_cost_change = 0.0
        total_resolution_change = 0.0
        total_risk_change = 0.0
        confidence_scores = []
        reasoning_parts = []
        
        # Process each action in the scenario
        for action in scenario.actions:
            impact = self._process_action(action)
            
            total_dqi_change += impact.get("dqi_change", 0)
            total_cost_change += impact.get("cost_change", 0)
            total_resolution_change += impact.get("query_resolution_change", 0)
            total_risk_change += impact.get("timeline_risk_change", 0)
            confidence_scores.append(impact.get("confidence", 0.8))
            reasoning_parts.append(impact.get("reasoning", ""))
            
        # Calculate predicted values (with bounds)
        predicted_dqi = max(0, min(100, baseline["avg_dqi"] + total_dqi_change))
        predicted_resolution = max(1, baseline["avg_query_resolution_days"] + total_resolution_change)
        predicted_risk = max(0, min(100, baseline["timeline_risk_percent"] + total_risk_change))
        
        # Average confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.8
        
        # Calculate ROI score (benefit per cost)
        if total_cost_change > 0:
            roi_score = (total_dqi_change * 1000 - total_risk_change * 500) / total_cost_change
        else:
            roi_score = total_dqi_change * 10  # If cost is zero or negative, high ROI
            
        # Create metric changes
        metric_changes = [
            MetricChange(
                metric_name="DQI Score",
                baseline_value=baseline["avg_dqi"],
                predicted_value=predicted_dqi,
                change=total_dqi_change,
                change_percent=(total_dqi_change / baseline["avg_dqi"]) * 100 if baseline["avg_dqi"] > 0 else 0,
                direction="improved" if total_dqi_change > 0 else ("declined" if total_dqi_change < 0 else "unchanged")
            ),
            MetricChange(
                metric_name="Query Resolution Time",
                baseline_value=baseline["avg_query_resolution_days"],
                predicted_value=predicted_resolution,
                change=total_resolution_change,
                change_percent=(total_resolution_change / baseline["avg_query_resolution_days"]) * 100,
                direction="improved" if total_resolution_change < 0 else ("declined" if total_resolution_change > 0 else "unchanged")
            ),
            MetricChange(
                metric_name="Timeline Risk",
                baseline_value=baseline["timeline_risk_percent"],
                predicted_value=predicted_risk,
                change=total_risk_change,
                change_percent=(total_risk_change / baseline["timeline_risk_percent"]) * 100 if baseline["timeline_risk_percent"] > 0 else 0,
                direction="improved" if total_risk_change < 0 else ("declined" if total_risk_change > 0 else "unchanged")
            )
        ]
        
        # Generate explanation
        explanation = self._generate_explanation(
            scenario, baseline,
            {"dqi": predicted_dqi, "resolution": predicted_resolution, "risk": predicted_risk},
            reasoning_parts
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(scenario, total_dqi_change, total_cost_change)
        
        # Generate risks
        risks = self._identify_risks(scenario, total_risk_change)
        
        return SimulationResult(
            scenario_name=scenario.name,
            scenario_description=scenario.description,
            baseline_dqi=round(baseline["avg_dqi"], 2),
            predicted_dqi=round(predicted_dqi, 2),
            dqi_change=round(total_dqi_change, 2),
            baseline_query_resolution_days=round(baseline["avg_query_resolution_days"], 2),
            predicted_query_resolution_days=round(predicted_resolution, 2),
            query_resolution_change=round(total_resolution_change, 2),
            baseline_timeline_risk=round(baseline["timeline_risk_percent"], 2),
            predicted_timeline_risk=round(predicted_risk, 2),
            timeline_risk_change=round(total_risk_change, 2),
            estimated_cost_change=round(total_cost_change, 2),
            roi_score=round(roi_score, 2),
            confidence_score=round(avg_confidence, 2),
            metric_changes=metric_changes,
            site_level_predictions={},
            explanation=explanation,
            recommendations=recommendations,
            risks=risks
        )
        
    def _process_action(self, action: ScenarioAction) -> Dict[str, float]:
        """Process a single scenario action and return its impact."""
        
        if action.action_type == ScenarioType.ADD_CRA:
            region_data = self.region_data.get(action.target, {"sites_count": 5, "cra_count": 4, "avg_dqi": 70})
            return self.impact_model.calculate_cra_impact(
                current_cras=region_data.get("cra_count", 4),
                cra_change=int(action.value),
                region=action.target,
                region_data=region_data
            )
            
        elif action.action_type == ScenarioType.REMOVE_CRA:
            region_data = self.region_data.get(action.target, {"sites_count": 5, "cra_count": 4, "avg_dqi": 70})
            return self.impact_model.calculate_cra_impact(
                current_cras=region_data.get("cra_count", 4),
                cra_change=-int(action.value),
                region=action.target,
                region_data=region_data
            )
            
        elif action.action_type == ScenarioType.INCREASE_MONITORING:
            return self.impact_model.calculate_monitoring_impact(
                current_frequency=self.trial_data.get("monitoring_frequency", 100),
                frequency_change_percent=action.value,
                target_scope=action.target,
                scope_data={"avg_dqi": self.trial_data.get("avg_dqi", 70)}
            )
            
        elif action.action_type == ScenarioType.DECREASE_MONITORING:
            return self.impact_model.calculate_monitoring_impact(
                current_frequency=self.trial_data.get("monitoring_frequency", 100),
                frequency_change_percent=-action.value,
                target_scope=action.target,
                scope_data={"avg_dqi": self.trial_data.get("avg_dqi", 70)}
            )
            
        elif action.action_type == ScenarioType.CLOSE_SITE:
            site_data = self.site_data.get(action.target, {"dqi": 50, "patient_count": 15, "operational_cost": 50000})
            return self.impact_model.calculate_site_closure_impact(
                site_id=action.target,
                site_data=site_data,
                trial_data=self.trial_data
            )
            
        elif action.action_type == ScenarioType.ADD_TRAINING:
            return self.impact_model.calculate_training_impact(
                training_sessions=int(action.value),
                target_scope=action.target,
                scope_data={"open_queries": self.trial_data.get("total_open_queries", 50)}
            )
            
        elif action.action_type == ScenarioType.EXTEND_TIMELINE:
            return self.impact_model.calculate_timeline_extension_impact(
                weeks_extension=int(action.value),
                trial_data=self.trial_data
            )
            
        return {"dqi_change": 0, "cost_change": 0, "query_resolution_change": 0, "timeline_risk_change": 0, "confidence": 0.5}
        
    def _generate_explanation(
        self,
        scenario: Scenario,
        baseline: Dict,
        predictions: Dict,
        reasoning_parts: List[str]
    ) -> str:
        """Generate human-readable explanation of simulation results."""
        
        if self.llm:
            return self._generate_llm_explanation(scenario, baseline, predictions)
            
        # Simple template-based explanation
        dqi_change = predictions["dqi"] - baseline["avg_dqi"]
        resolution_change = predictions["resolution"] - baseline["avg_query_resolution_days"]
        risk_change = predictions["risk"] - baseline["timeline_risk_percent"]
        
        parts = [f"**Scenario: {scenario.name}**\n"]
        
        # DQI Analysis
        if dqi_change > 0:
            parts.append(f"✅ Data Quality Index is predicted to **improve by {dqi_change:.1f} points** (from {baseline['avg_dqi']:.1f} to {predictions['dqi']:.1f}).")
        elif dqi_change < 0:
            parts.append(f"⚠️ Data Quality Index is predicted to **decline by {abs(dqi_change):.1f} points** (from {baseline['avg_dqi']:.1f} to {predictions['dqi']:.1f}).")
        else:
            parts.append("➡️ Data Quality Index is expected to remain stable.")
            
        # Resolution Analysis
        if resolution_change < 0:
            parts.append(f"✅ Query resolution time expected to **decrease by {abs(resolution_change):.1f} days**.")
        elif resolution_change > 0:
            parts.append(f"⚠️ Query resolution time may **increase by {resolution_change:.1f} days**.")
            
        # Risk Analysis
        if risk_change < 0:
            parts.append(f"✅ Timeline risk is predicted to **reduce by {abs(risk_change):.1f}%** (from {baseline['timeline_risk_percent']:.1f}% to {predictions['risk']:.1f}%).")
        elif risk_change > 0:
            parts.append(f"⚠️ Timeline risk may **increase by {risk_change:.1f}%**.")
            
        return "\n\n".join(parts)
        
    def _generate_llm_explanation(self, scenario: Scenario, baseline: Dict, predictions: Dict) -> str:
        """Generate explanation using LLM."""
        prompt = f"""
        Explain the results of this clinical trial simulation concisely:
        
        SCENARIO: {scenario.name}
        ACTIONS: {[f"{a.action_type.value}: {a.target} by {a.value}" for a in scenario.actions]}
        
        BASELINE → PREDICTED:
        - DQI: {baseline['avg_dqi']:.1f} → {predictions['dqi']:.1f}
        - Query Resolution: {baseline['avg_query_resolution_days']:.1f} days → {predictions['resolution']:.1f} days
        - Timeline Risk: {baseline['timeline_risk_percent']:.1f}% → {predictions['risk']:.1f}%
        
        Provide a brief 2-3 sentence explanation of:
        1. What the changes mean in practical terms
        2. Key trade-offs to consider
        """
        
        try:
            return self.llm.invoke(prompt)
        except Exception as e:
            logger.error(f"LLM explanation failed: {e}")
            return self._generate_explanation(scenario, baseline, predictions, [])
            
    def _generate_recommendations(self, scenario: Scenario, dqi_change: float, cost_change: float) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if dqi_change > 5:
            recommendations.append("📈 This scenario shows strong DQI improvement potential. Consider implementing these changes.")
            
        if dqi_change > 0 and cost_change < 0:
            recommendations.append("💰 This is a win-win scenario: improved quality with cost savings!")
            
        if dqi_change > 0 and cost_change > 0:
            if dqi_change / (cost_change / 10000) > 0.5:
                recommendations.append("✅ The ROI appears favorable - quality improvements justify the cost.")
            else:
                recommendations.append("⚖️ Consider whether the quality gains justify the cost increase.")
                
        if not recommendations:
            recommendations.append("📊 Review the detailed metrics to assess if this scenario aligns with trial priorities.")
            
        return recommendations
        
    def _identify_risks(self, scenario: Scenario, risk_change: float) -> List[str]:
        """Identify potential risks from the scenario."""
        risks = []
        
        for action in scenario.actions:
            if action.action_type == ScenarioType.CLOSE_SITE:
                risks.append(f"⚠️ Closing {action.target} requires patient transfers - plan carefully.")
                
            if action.action_type == ScenarioType.REMOVE_CRA:
                risks.append(f"⚠️ Reducing CRAs in {action.target} may strain remaining staff.")
                
            if action.action_type == ScenarioType.DECREASE_MONITORING:
                risks.append("⚠️ Reduced monitoring may delay issue detection.")
                
        if risk_change > 10:
            risks.append("🚨 High timeline risk increase - consider mitigation strategies.")
            
        return risks
        
    def compare_scenarios(self, scenarios: List[Scenario]) -> ScenarioComparison:
        """Compare multiple scenarios side-by-side."""
        results = [self.run_simulation(scenario) for scenario in scenarios]
        
        # Find best scenario for each metric
        best_dqi = max(results, key=lambda r: r.predicted_dqi)
        best_cost = min(results, key=lambda r: r.estimated_cost_change)
        best_risk = min(results, key=lambda r: r.predicted_timeline_risk)
        
        # Overall recommendation (weighted scoring)
        def score_scenario(r: SimulationResult) -> float:
            return (r.dqi_change * 2) - (r.timeline_risk_change * 1.5) - (r.estimated_cost_change / 50000)
            
        recommended = max(results, key=score_scenario)
        
        return ScenarioComparison(
            scenarios=results,
            best_for_dqi=best_dqi.scenario_name,
            best_for_cost=best_cost.scenario_name,
            best_for_risk=best_risk.scenario_name,
            recommended_scenario=recommended.scenario_name,
            recommendation_reason=f"Best balance of DQI improvement ({recommended.dqi_change:+.1f}) and risk reduction ({recommended.timeline_risk_change:+.1f}%)"
        )
        
    def get_available_regions(self) -> List[str]:
        """Get list of available regions for simulation."""
        return list(self.region_data.keys())
        
    def get_available_sites(self) -> List[str]:
        """Get list of available sites for simulation."""
        return list(self.site_data.keys())
        
    def get_preset_scenarios(self) -> List[Scenario]:
        """Get common preset scenarios for quick testing."""
        regions = self.get_available_regions()
        sites = self.get_available_sites()
        
        presets = []
        
        # Preset 1: Add CRA support
        if regions:
            presets.append(Scenario(
                name="Add CRA Support",
                description="Add 2 CRAs to regions with highest workload",
                actions=[ScenarioAction(ScenarioType.ADD_CRA, regions[0], 2)]
            ))
            
        # Preset 2: Increase monitoring
        presets.append(Scenario(
            name="Increase Monitoring 25%",
            description="Increase monitoring frequency by 25% across all sites",
            actions=[ScenarioAction(ScenarioType.INCREASE_MONITORING, "All Sites", 25)]
        ))
        
        # Preset 3: Add training
        presets.append(Scenario(
            name="Data Entry Training",
            description="Add training sessions for data entry best practices",
            actions=[ScenarioAction(ScenarioType.ADD_TRAINING, "All Sites", 2)]
        ))
        
        # Preset 4: Aggressive improvement
        if regions:
            presets.append(Scenario(
                name="Aggressive Improvement",
                description="Combined approach: more CRAs, more monitoring, and training",
                actions=[
                    ScenarioAction(ScenarioType.ADD_CRA, regions[0], 2),
                    ScenarioAction(ScenarioType.INCREASE_MONITORING, "All Sites", 20),
                    ScenarioAction(ScenarioType.ADD_TRAINING, "All Sites", 1)
                ]
            ))
            
        # Preset 5: Cost optimization
        presets.append(Scenario(
            name="Cost Optimization",
            description="Reduce monitoring slightly while adding targeted training",
            actions=[
                ScenarioAction(ScenarioType.DECREASE_MONITORING, "All Sites", 10),
                ScenarioAction(ScenarioType.ADD_TRAINING, "High-Risk Sites", 2)
            ]
        ))
        
        return presets
