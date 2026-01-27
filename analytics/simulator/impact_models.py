"""Impact Models for Digital Twin Simulator.

These models calculate how different actions affect clinical trial metrics.
Coefficients can be:
1. Learned from historical data
2. Set by domain experts
3. Calibrated based on trial-specific characteristics
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np


@dataclass
class ImpactCoefficients:
    """
    Coefficients that define how changes affect outcomes.
    These represent the "physics" of the clinical trial simulation.
    
    Positive values = improvement, Negative values = decline
    """
    
    # CRA Impact Coefficients
    cra_to_query_resolution: float = -0.8  # Each CRA reduces resolution time by 0.8 days
    cra_to_dqi: float = 2.5  # Each CRA improves DQI by 2.5 points
    cra_to_site_response: float = 1.5  # Each CRA improves site response by 1.5%
    cra_annual_cost: float = 85000  # Annual cost per CRA (USD)
    
    # Monitoring Frequency Impact
    monitoring_freq_to_dqi: float = 0.12  # Each 1% increase = 0.12 DQI improvement
    monitoring_freq_to_query_resolution: float = -0.05  # Each 1% = 0.05 days faster
    monitoring_freq_to_cost: float = 450  # Each 1% increase = $450 cost
    
    # Site Closure Impact
    poor_site_removal_dqi_boost: float = 2.5  # Closing poor site improves avg DQI
    patient_transfer_risk: float = 0.3  # Risk factor per patient transferred
    site_closure_savings: float = 45000  # Average savings from closing a site
    
    # Training Impact
    training_to_dqi: float = 4.0  # Training session improves DQI by 4 points
    training_to_query_resolution: float = -1.2  # Training reduces resolution by 1.2 days
    training_session_cost: float = 8000  # Cost per training session
    
    # Timeline Extension Impact
    timeline_extension_to_risk: float = -2.0  # Each week extension reduces risk by 2%
    timeline_extension_cost: float = 25000  # Cost per week of extension
    
    # Diminishing returns thresholds
    dqi_diminishing_threshold: float = 85  # Benefits reduce above this DQI
    monitoring_saturation: float = 150  # % above which more monitoring has minimal effect


class ImpactModel:
    """
    Model that calculates the impact of scenario changes on trial metrics.
    
    This is the "brain" of the Digital Twin - it encodes domain knowledge
    about how different actions affect clinical trial outcomes.
    """
    
    def __init__(self, coefficients: ImpactCoefficients = None):
        self.coef = coefficients or ImpactCoefficients()
        
    def calculate_cra_impact(
        self, 
        current_cras: int, 
        cra_change: int, 
        region: str,
        region_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate impact of adding/removing CRAs in a region.
        
        Args:
            current_cras: Current number of CRAs in region
            cra_change: Number of CRAs to add (positive) or remove (negative)
            region: Region name/identifier
            region_data: Current metrics for the region
        
        Returns:
            Dict with predicted changes for each metric
        """
        # Base calculations
        dqi_change = cra_change * self.coef.cra_to_dqi
        resolution_change = cra_change * self.coef.cra_to_query_resolution
        response_change = cra_change * self.coef.cra_to_site_response
        
        # Adjust based on current workload (overloaded regions benefit more)
        sites_per_cra = region_data.get("sites_count", 10) / max(current_cras, 1)
        workload_factor = min(sites_per_cra / 5, 2.0)  # Cap at 2x boost
        
        if workload_factor > 1.0 and cra_change > 0:
            # Overloaded region benefits more from additional CRAs
            dqi_change *= workload_factor
            resolution_change *= workload_factor
            
        # Diminishing returns for high-performing regions
        current_dqi = region_data.get("avg_dqi", 70)
        if current_dqi > self.coef.dqi_diminishing_threshold:
            diminishing_factor = 0.5
            dqi_change *= diminishing_factor
            
        # Cost calculation
        cost_change = cra_change * self.coef.cra_annual_cost
        
        # Timeline risk reduction
        risk_change = -abs(cra_change) * 1.5 if cra_change > 0 else abs(cra_change) * 2.0
        
        return {
            "dqi_change": round(dqi_change, 2),
            "query_resolution_change": round(resolution_change, 2),
            "site_response_change": round(response_change, 2),
            "timeline_risk_change": round(risk_change, 2),
            "cost_change": round(cost_change, 2),
            "confidence": 0.85,
            "reasoning": f"Adding {cra_change} CRA(s) to {region} with workload factor {workload_factor:.1f}"
        }
    
    def calculate_monitoring_impact(
        self,
        current_frequency: float,
        frequency_change_percent: float,
        target_scope: str,
        scope_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate impact of changing monitoring frequency.
        
        Args:
            current_frequency: Current monitoring frequency (as % of baseline)
            frequency_change_percent: Percentage change (e.g., 25 for 25% increase)
            target_scope: "All Sites", specific region, or site
            scope_data: Current metrics for the scope
        """
        # Check for saturation
        new_frequency = current_frequency + frequency_change_percent
        if new_frequency > self.coef.monitoring_saturation:
            # Apply diminishing returns
            effective_change = frequency_change_percent * 0.3
        else:
            effective_change = frequency_change_percent
            
        dqi_change = effective_change * self.coef.monitoring_freq_to_dqi
        resolution_change = effective_change * self.coef.monitoring_freq_to_query_resolution
        cost_change = effective_change * self.coef.monitoring_freq_to_cost
        
        # Risk reduction
        risk_change = -effective_change * 0.15
        
        # Already well-performing sites benefit less
        current_dqi = scope_data.get("avg_dqi", 70)
        if current_dqi > self.coef.dqi_diminishing_threshold:
            dqi_change *= 0.4
            
        return {
            "dqi_change": round(dqi_change, 2),
            "query_resolution_change": round(resolution_change, 2),
            "timeline_risk_change": round(risk_change, 2),
            "cost_change": round(cost_change, 2),
            "confidence": 0.80,
            "reasoning": f"Changing monitoring by {frequency_change_percent}% for {target_scope}"
        }
    
    def calculate_site_closure_impact(
        self,
        site_id: str,
        site_data: Dict[str, Any],
        trial_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate impact of closing a site.
        
        Args:
            site_id: Site identifier
            site_data: Current metrics for the site
            trial_data: Overall trial metrics
        """
        site_dqi = site_data.get("dqi", 50)
        avg_dqi = trial_data.get("avg_dqi", 70)
        patient_count = site_data.get("patient_count", 0)
        
        # If site is below average, closing it improves overall DQI
        if site_dqi < avg_dqi:
            dqi_change = (avg_dqi - site_dqi) * 0.08 * self.coef.poor_site_removal_dqi_boost
        else:
            # Negative impact - we're closing a good site
            dqi_change = -((site_dqi - avg_dqi) * 0.1)
            
        # Patient transfer risk
        timeline_risk_change = patient_count * self.coef.patient_transfer_risk
        
        # Cost savings from closing site
        operational_cost = site_data.get("operational_cost", self.coef.site_closure_savings)
        cost_change = -operational_cost  # Negative = savings
        
        # Query resolution might worsen if patients transfer to busy sites
        resolution_change = patient_count * 0.1
        
        return {
            "dqi_change": round(dqi_change, 2),
            "query_resolution_change": round(resolution_change, 2),
            "timeline_risk_change": round(timeline_risk_change, 2),
            "cost_change": round(cost_change, 2),
            "confidence": 0.70,  # Lower confidence - complex decision
            "reasoning": f"Closing {site_id} with DQI {site_dqi} (avg: {avg_dqi}), {patient_count} patients"
        }
    
    def calculate_training_impact(
        self,
        training_sessions: int,
        target_scope: str,
        scope_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate impact of adding training sessions.
        
        Args:
            training_sessions: Number of training sessions to add
            target_scope: Sites/regions receiving training
            scope_data: Current metrics for the scope
        """
        dqi_change = training_sessions * self.coef.training_to_dqi
        resolution_change = training_sessions * self.coef.training_to_query_resolution
        cost_change = training_sessions * self.coef.training_session_cost
        
        # Training has delayed effect - builds over time
        risk_change = -training_sessions * 0.8
        
        # Sites with more issues benefit more from training
        open_queries = scope_data.get("open_queries", 0)
        if open_queries > 50:
            dqi_change *= 1.3
            resolution_change *= 1.3
            
        return {
            "dqi_change": round(dqi_change, 2),
            "query_resolution_change": round(resolution_change, 2),
            "timeline_risk_change": round(risk_change, 2),
            "cost_change": round(cost_change, 2),
            "confidence": 0.75,
            "reasoning": f"Adding {training_sessions} training session(s) for {target_scope}"
        }
    
    def calculate_timeline_extension_impact(
        self,
        weeks_extension: int,
        trial_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate impact of extending trial timeline.
        
        Args:
            weeks_extension: Number of weeks to extend
            trial_data: Current trial metrics
        """
        risk_change = weeks_extension * self.coef.timeline_extension_to_risk
        cost_change = weeks_extension * self.coef.timeline_extension_cost
        
        # More time allows for better data quality
        dqi_change = weeks_extension * 1.5
        resolution_change = 0  # Doesn't directly affect resolution time
        
        return {
            "dqi_change": round(dqi_change, 2),
            "query_resolution_change": round(resolution_change, 2),
            "timeline_risk_change": round(risk_change, 2),
            "cost_change": round(cost_change, 2),
            "confidence": 0.90,  # High confidence - direct relationship
            "reasoning": f"Extending timeline by {weeks_extension} week(s)"
        }


def create_custom_coefficients(
    trial_type: str = "standard",
    therapeutic_area: str = "general"
) -> ImpactCoefficients:
    """
    Create custom coefficients based on trial characteristics.
    
    Different trial types and therapeutic areas have different dynamics.
    """
    coef = ImpactCoefficients()
    
    # Oncology trials typically need more monitoring
    if therapeutic_area.lower() == "oncology":
        coef.monitoring_freq_to_dqi *= 1.3
        coef.cra_to_dqi *= 1.2
        coef.cra_annual_cost *= 1.15  # Higher specialized costs
        
    # Rare disease trials have fewer patients, different dynamics
    if trial_type.lower() == "rare_disease":
        coef.patient_transfer_risk *= 2.0  # Each patient matters more
        coef.site_closure_savings *= 0.7  # Smaller sites
        
    # Phase 1 trials are more intensive
    if trial_type.lower() == "phase1":
        coef.monitoring_freq_to_dqi *= 1.5
        coef.training_to_dqi *= 1.4
        
    return coef
