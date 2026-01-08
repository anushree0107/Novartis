from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from analytics.risk.detector import SiteAnomalyDetector
from analytics.risk.enhanced_detector import (
    EnhancedAnomalyDetector,
    AnomalyMethod,
    AnomalyScore,
    ControlChartResult,
    DriftResult
)
from analytics.risk.llm import RiskValidator

router = APIRouter()

# Instances
legacy_detector = SiteAnomalyDetector()
enhanced_detector = EnhancedAnomalyDetector()
validator = RiskValidator()


# ============ UI Color Mapping ============

RISK_COLORS = {
    "Critical": {
        "bg": "#DC2626", 
        "text": "#FFFFFF", 
        "border": "#B91C1C", 
        "gradient": "linear-gradient(135deg, #DC2626 0%, #991B1B 100%)",
        "glow": "0 0 20px rgba(220, 38, 38, 0.5)",
        "icon": "🔴",
        "badge_class": "bg-red-600"
    },
    "High": {
        "bg": "#F97316", 
        "text": "#FFFFFF", 
        "border": "#EA580C", 
        "gradient": "linear-gradient(135deg, #F97316 0%, #C2410C 100%)",
        "glow": "0 0 20px rgba(249, 115, 22, 0.5)",
        "icon": "🟠",
        "badge_class": "bg-orange-500"
    },
    "Medium": {
        "bg": "#EAB308", 
        "text": "#1F2937", 
        "border": "#CA8A04", 
        "gradient": "linear-gradient(135deg, #EAB308 0%, #A16207 100%)",
        "glow": "0 0 20px rgba(234, 179, 8, 0.5)",
        "icon": "🟡",
        "badge_class": "bg-yellow-500"
    },
    "Low": {
        "bg": "#22C55E", 
        "text": "#FFFFFF", 
        "border": "#16A34A", 
        "gradient": "linear-gradient(135deg, #22C55E 0%, #15803D 100%)",
        "glow": "0 0 20px rgba(34, 197, 94, 0.5)",
        "icon": "🟢",
        "badge_class": "bg-green-500"
    }
}

# Anomaly score to gauge color
def get_gauge_color(score: float) -> str:
    if score >= 0.3:
        return "#DC2626"
    elif score >= 0.2:
        return "#F97316"
    elif score >= 0.1:
        return "#EAB308"
    return "#22C55E"


# ============ Pydantic Models ============

class UIAnomalyScore(BaseModel):
    entity_id: str
    entity_type: str
    is_anomaly: bool
    anomaly_score: float
    anomaly_score_pct: float
    risk_level: str
    risk_color: Dict[str, str]
    method_scores: Dict[str, float]
    feature_contributions: List[Dict[str, Any]]
    anomalous_features: List[str]
    explanation: str
    # UI extras
    gauge_color: str
    rank: int
    score_label: str


class UIControlChart(BaseModel):
    metric_name: str
    metric_display_name: str
    current_value: float
    formatted_value: str
    mean: float
    std: float
    ucl: float
    lcl: float
    usl: float
    lsl: float
    is_out_of_control: bool
    violation_type: Optional[str]
    status_color: str
    status_icon: str
    # For visualization
    chart_data: Dict[str, Any]


class UIRiskSummary(BaseModel):
    total_sites: int
    anomaly_count: int
    anomaly_rate: float
    anomaly_rate_formatted: str
    risk_distribution: List[Dict[str, Any]]
    top_anomalous_features: List[Dict[str, Any]]
    top_anomalies: List[UIAnomalyScore]
    # Chart data
    distribution_chart: Dict[str, Any]
    heatmap_data: Dict[str, Any]
    trend_indicator: Dict[str, Any]


class UISiteRiskDetail(BaseModel):
    site_id: str
    anomaly_score: float
    risk_level: str
    risk_color: Dict[str, str]
    is_anomaly: bool
    explanation: str
    # Detailed breakdown
    method_scores_chart: Dict[str, Any]
    feature_contributions_chart: Dict[str, Any]
    control_charts: List[UIControlChart]
    recommendations: List[str]
    similar_risk_sites: List[Dict[str, Any]]


class UIDashboard(BaseModel):
    summary: UIRiskSummary
    risk_matrix: Dict[str, Any]
    alert_count: Dict[str, int]
    recent_anomalies: List[UIAnomalyScore]


# ============ Helper Functions ============

def format_feature_contribution(name: str, value: float, raw_value: float) -> Dict[str, Any]:
    display_name = name.replace("_", " ").title()
    
    if "_pct" in name:
        formatted = f"{raw_value * 100:.1f}%"
    elif "days" in name:
        formatted = f"{raw_value:.1f} days"
    else:
        formatted = f"{raw_value:.2f}"
    
    # Severity based on contribution
    if value >= 0.7:
        severity = "critical"
        color = "#DC2626"
    elif value >= 0.5:
        severity = "high"
        color = "#F97316"
    elif value >= 0.3:
        severity = "medium"
        color = "#EAB308"
    else:
        severity = "low"
        color = "#22C55E"
    
    return {
        "name": display_name,
        "raw_name": name,
        "contribution": round(value * 100, 1),
        "raw_value": raw_value,
        "formatted_value": formatted,
        "severity": severity,
        "color": color,
        "bar_width": min(value * 100, 100)
    }

def score_to_label(score: float) -> str:
    if score >= 0.5:
        return "Severe"
    elif score >= 0.3:
        return "High"
    elif score >= 0.2:
        return "Elevated"
    elif score >= 0.1:
        return "Moderate"
    return "Normal"

def build_ui_anomaly(result: AnomalyScore, rank: int) -> UIAnomalyScore:
    risk_color = RISK_COLORS.get(result.risk_level, RISK_COLORS["Low"])
    
    # Build feature contributions list
    feature_contribs = []
    for name, contrib in sorted(result.feature_contributions.items(), key=lambda x: x[1], reverse=True):
        raw_val = result.features.get(name, 0)
        feature_contribs.append(format_feature_contribution(name, contrib, raw_val))
    
    return UIAnomalyScore(
        entity_id=result.entity_id,
        entity_type=result.entity_type,
        is_anomaly=result.is_anomaly,
        anomaly_score=round(result.anomaly_score, 4),
        anomaly_score_pct=round(result.anomaly_score * 100, 1),
        risk_level=result.risk_level,
        risk_color=risk_color,
        method_scores={k: round(v, 4) for k, v in result.method_scores.items()},
        feature_contributions=feature_contribs[:6],
        anomalous_features=result.anomalous_features[:5],
        explanation=result.explanation,
        gauge_color=get_gauge_color(result.anomaly_score),
        rank=rank,
        score_label=score_to_label(result.anomaly_score)
    )


def build_ui_control_chart(result: ControlChartResult) -> UIControlChart:
    display_name = result.metric_name.replace("_", " ").title()
    
    # Format value
    if "_pct" in result.metric_name:
        formatted = f"{result.current_value * 100:.1f}%"
    elif "days" in result.metric_name:
        formatted = f"{result.current_value:.1f} days"
    else:
        formatted = f"{result.current_value:.2f}"
    
    # Status
    if result.is_out_of_control:
        if "usl" in (result.violation_type or ""):
            status_color = "#DC2626"
            status_icon = "⚠️"
        elif "ucl" in (result.violation_type or ""):
            status_color = "#F97316"
            status_icon = "⚡"
        else:
            status_color = "#EAB308"
            status_icon = "📉"
    else:
        status_color = "#22C55E"
        status_icon = "✅"
    
    # Chart data for control chart visualization
    chart_data = {
        "type": "control_chart",
        "current": result.current_value,
        "mean": result.mean,
        "ucl": result.ucl,
        "lcl": result.lcl,
        "usl": result.usl,
        "lsl": result.lsl,
        "zones": [
            {"name": "USL", "value": result.usl, "color": "#DC2626"},
            {"name": "UCL", "value": result.ucl, "color": "#F97316"},
            {"name": "Mean", "value": result.mean, "color": "#3B82F6"},
            {"name": "LCL", "value": result.lcl, "color": "#F97316"},
            {"name": "LSL", "value": result.lsl, "color": "#DC2626"},
        ]
    }
    
    return UIControlChart(
        metric_name=result.metric_name,
        metric_display_name=display_name,
        current_value=result.current_value,
        formatted_value=formatted,
        mean=result.mean,
        std=result.std,
        ucl=result.ucl,
        lcl=result.lcl,
        usl=result.usl,
        lsl=result.lsl,
        is_out_of_control=result.is_out_of_control,
        violation_type=result.violation_type,
        status_color=status_color,
        status_icon=status_icon,
        chart_data=chart_data
    )


# ============ Legacy Endpoints ============

@router.get("/sites")
def get_site_risks():
    """Get risk assessment for all sites (legacy)."""
    results = legacy_detector.predict()
    if not results:
        success = legacy_detector.train()
        if success:
            results = legacy_detector.predict()
    return {"sites": results, "count": len(results)}


@router.get("/site/{site_id}")
def get_site_risk_detail(site_id: str, explain: bool = False):
    """Get risk detail for a specific site (legacy)."""
    result = legacy_detector.get_site_risk(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Site not found in risk model")

    if explain:
        stats = legacy_detector.get_population_stats()
        explanation = validator.generate_explanation(site_id, result, stats)
        result["explanation"] = explanation
        
    return result


@router.post("/train")
def train_model():
    """Train the legacy risk model."""
    success = legacy_detector.train()
    if success:
        return {"status": "success", "message": "Model trained successfully"}
    else:
        raise HTTPException(status_code=500, detail="Training failed")


# ============ UI-Ready Enhanced Endpoints ============

@router.get("/enhanced/dashboard", response_model=UIDashboard)
async def get_risk_dashboard():
    """
    Get complete risk monitoring dashboard data.
    
    Returns all data needed for a comprehensive risk visualization dashboard.
    """
    results = enhanced_detector.detect_anomalies()
    
    if not results:
        enhanced_detector.train()
        results = enhanced_detector.detect_anomalies()
    
    total_sites = len(results)
    anomaly_count = sum(1 for r in results if r.is_anomaly)
    
    # Risk distribution
    risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for r in results:
        risk_counts[r.risk_level] = risk_counts.get(r.risk_level, 0) + 1
    
    risk_distribution = [
        {
            "level": level,
            "count": count,
            "percentage": round(count / total_sites * 100, 1) if total_sites > 0 else 0,
            "color": RISK_COLORS[level]["bg"],
            "icon": RISK_COLORS[level]["icon"]
        }
        for level, count in risk_counts.items()
    ]
    
    # Distribution chart (donut)
    distribution_chart = {
        "type": "donut",
        "data": [
            {"name": level, "value": count, "color": RISK_COLORS[level]["bg"]}
            for level, count in risk_counts.items() if count > 0
        ],
        "total": total_sites,
        "center_label": f"{risk_counts['Critical'] + risk_counts['High']} High Risk"
    }
    
    # Top anomalous features
    feature_counts: Dict[str, int] = {}
    for r in results:
        for feat in r.anomalous_features:
            feature_counts[feat] = feature_counts.get(feat, 0) + 1
    
    top_features = [
        {
            "name": feat.replace("_", " ").title(),
            "raw_name": feat,
            "count": count,
            "percentage": round(count / total_sites * 100, 1) if total_sites > 0 else 0,
            "bar_width": min(count / max(feature_counts.values(), default=1) * 100, 100)
        }
        for feat, count in sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    ]
    
    # Build UI anomalies
    top_anomalies = [build_ui_anomaly(r, i+1) for i, r in enumerate(results[:10])]
    
    # Heatmap data (feature x risk level)
    heatmap_data = {
        "type": "heatmap",
        "x_labels": ["Critical", "High", "Medium", "Low"],
        "y_labels": [f["name"] for f in top_features[:5]],
        "data": []  # Would need actual cross-tabulation
    }
    
    # Trend indicator
    trend_indicator = {
        "direction": "stable",  # Would need historical data
        "change": 0,
        "period": "7 days",
        "icon": "→"
    }
    
    summary = UIRiskSummary(
        total_sites=total_sites,
        anomaly_count=anomaly_count,
        anomaly_rate=anomaly_count / total_sites if total_sites > 0 else 0,
        anomaly_rate_formatted=f"{anomaly_count / total_sites * 100:.1f}%" if total_sites > 0 else "0%",
        risk_distribution=risk_distribution,
        top_anomalous_features=top_features,
        top_anomalies=top_anomalies,
        distribution_chart=distribution_chart,
        heatmap_data=heatmap_data,
        trend_indicator=trend_indicator
    )
    
    # Risk matrix (severity x likelihood)
    risk_matrix = {
        "type": "matrix",
        "rows": ["Critical", "High", "Medium", "Low"],
        "cols": ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"],
        "data": [
            [0, 0, risk_counts["Critical"]//4, risk_counts["Critical"]//2, risk_counts["Critical"]//4],
            [0, risk_counts["High"]//3, risk_counts["High"]//3, risk_counts["High"]//3, 0],
            [risk_counts["Medium"]//4, risk_counts["Medium"]//4, risk_counts["Medium"]//4, risk_counts["Medium"]//4, 0],
            [risk_counts["Low"]//2, risk_counts["Low"]//2, 0, 0, 0]
        ]
    }
    
    # Alert counts
    alert_count = {
        "critical": risk_counts["Critical"],
        "high": risk_counts["High"],
        "warning": risk_counts["Medium"],
        "info": risk_counts["Low"]
    }
    
    return UIDashboard(
        summary=summary,
        risk_matrix=risk_matrix,
        alert_count=alert_count,
        recent_anomalies=top_anomalies[:5]
    )


@router.get("/enhanced/anomalies", response_model=List[UIAnomalyScore])
async def get_enhanced_anomalies_ui(
    method: str = Query("ensemble", description="Detection method"),
    limit: int = Query(50, description="Max results"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level")
):
    """Get UI-ready anomaly scores for all sites."""
    try:
        method_enum = AnomalyMethod(method) if method in [m.value for m in AnomalyMethod] else AnomalyMethod.ENSEMBLE
    except ValueError:
        method_enum = AnomalyMethod.ENSEMBLE
    
    results = enhanced_detector.detect_anomalies(method=method_enum)
    
    if not results:
        enhanced_detector.train()
        results = enhanced_detector.detect_anomalies(method=method_enum)
    
    # Filter by risk level if specified
    if risk_level:
        results = [r for r in results if r.risk_level == risk_level]
    
    return [build_ui_anomaly(r, i+1) for i, r in enumerate(results[:limit])]


@router.get("/enhanced/site/{site_id}", response_model=UISiteRiskDetail)
async def get_site_risk_detail_ui(site_id: str):
    """Get comprehensive UI-ready risk detail for a site."""
    try:
        result = enhanced_detector.get_site_risk(site_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Site {site_id} not found in risk model")
        
        risk_color = RISK_COLORS.get(result.risk_level, RISK_COLORS["Low"])
        
        # Method scores chart (radar)
        method_scores_chart = {
            "type": "radar",
            "labels": [m.replace("_", " ").title() for m in result.method_scores.keys()],
            "data": [round(v * 100, 1) for v in result.method_scores.values()],
            "color": risk_color["bg"]
        }
        
        # Feature contributions chart (horizontal bar)
        feature_contribs = []
        for name, contrib in sorted(result.feature_contributions.items(), key=lambda x: x[1], reverse=True):
            raw_val = result.features.get(name, 0)
            feature_contribs.append(format_feature_contribution(name, contrib, raw_val))
        
        feature_contributions_chart = {
            "type": "horizontal_bar",
            "data": feature_contribs[:8]
        }
        
        # Control charts
        control_results = enhanced_detector.control_chart_analysis(site_id)
        control_charts = [build_ui_control_chart(c) for c in control_results] if control_results else []
    
        # Recommendations based on anomalous features
        recommendations = []
        for feat in result.anomalous_features[:3]:
            if "missing_visits" in feat:
                recommendations.append("Schedule site visit to address missing visit data")
            elif "missing_pages" in feat:
                recommendations.append("Review CRF completion process with site staff")
            elif "open_issues" in feat:
                recommendations.append("Prioritize query resolution through targeted follow-up")
            elif "safety" in feat:
                recommendations.append("URGENT: Expedite pending safety reviews")
            elif "days" in feat:
                recommendations.append("Address aged data issues through site engagement")
        
        if not recommendations:
            recommendations.append("Continue routine monitoring")
        
        # Similar risk sites
        all_results = enhanced_detector.detect_anomalies()
        similar = [
            {"site_id": r.entity_id, "risk_level": r.risk_level, "score": round(r.anomaly_score, 3)}
            for r in all_results 
            if r.risk_level == result.risk_level and r.entity_id != site_id
        ][:5]
        
        return UISiteRiskDetail(
            site_id=site_id,
            anomaly_score=round(result.anomaly_score, 4),
            risk_level=result.risk_level,
            risk_color=risk_color,
            is_anomaly=result.is_anomaly,
            explanation=result.explanation,
            method_scores_chart=method_scores_chart,
            feature_contributions_chart=feature_contributions_chart,
            control_charts=control_charts,
            recommendations=recommendations,
            similar_risk_sites=similar
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting risk for {site_id}: {str(e)}")


@router.get("/enhanced/high-risk", response_model=List[UIAnomalyScore])
async def get_high_risk_sites_ui(
    threshold: str = Query("High", description="Minimum risk level")
):
    """Get UI-ready list of high-risk sites."""
    valid_thresholds = ["Critical", "High", "Medium", "Low"]
    if threshold not in valid_thresholds:
        raise HTTPException(status_code=400, detail=f"Invalid threshold")
    
    results = enhanced_detector.get_high_risk_sites(threshold=threshold)
    return [build_ui_anomaly(r, i+1) for i, r in enumerate(results)]


@router.get("/enhanced/control-chart/{site_id}", response_model=List[UIControlChart])
async def get_control_charts_ui(site_id: str):
    """Get UI-ready control chart data for a site."""
    results = enhanced_detector.control_chart_analysis(site_id)
    
    if not results:
        raise HTTPException(status_code=404, detail=f"No data for site {site_id}")
    
    return [build_ui_control_chart(r) for r in results]


@router.get("/enhanced/summary", response_model=UIRiskSummary)
async def get_risk_summary_ui():
    """Get UI-ready risk summary."""
    results = enhanced_detector.detect_anomalies()
    
    total_sites = len(results)
    anomaly_count = sum(1 for r in results if r.is_anomaly)
    
    risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for r in results:
        risk_counts[r.risk_level] = risk_counts.get(r.risk_level, 0) + 1
    
    risk_distribution = [
        {
            "level": level,
            "count": count,
            "percentage": round(count / total_sites * 100, 1) if total_sites > 0 else 0,
            "color": RISK_COLORS[level]["bg"],
            "icon": RISK_COLORS[level]["icon"]
        }
        for level, count in risk_counts.items()
    ]
    
    distribution_chart = {
        "type": "donut",
        "data": [{"name": level, "value": count, "color": RISK_COLORS[level]["bg"]} for level, count in risk_counts.items()]
    }
    
    feature_counts: Dict[str, int] = {}
    for r in results:
        for feat in r.anomalous_features:
            feature_counts[feat] = feature_counts.get(feat, 0) + 1
    
    top_features = [
        {"name": feat.replace("_", " ").title(), "count": count}
        for feat, count in sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    top_anomalies = [build_ui_anomaly(r, i+1) for i, r in enumerate(results[:5])]
    
    return UIRiskSummary(
        total_sites=total_sites,
        anomaly_count=anomaly_count,
        anomaly_rate=anomaly_count / total_sites if total_sites > 0 else 0,
        anomaly_rate_formatted=f"{anomaly_count / total_sites * 100:.1f}%",
        risk_distribution=risk_distribution,
        top_anomalous_features=top_features,
        top_anomalies=top_anomalies,
        distribution_chart=distribution_chart,
        heatmap_data={},
        trend_indicator={"direction": "stable", "change": 0}
    )


@router.post("/enhanced/train")
async def train_enhanced_models():
    success = enhanced_detector.train()
    
    if success:
        return {
            "status": "success",
            "message": "Models trained successfully",
            "models_trained": ["isolation_forest", "lof", "elliptic_envelope"],
            "icon": "✅"
        }
    raise HTTPException(status_code=500, detail="Training failed")
