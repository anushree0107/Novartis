from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()


# ============ UI Color & Icons ============

PERFORMANCE_COLORS = {
    "top_performer": {"bg": "#22C55E", "text": "#FFFFFF", "icon": "🏆", "label": "Top Performer"},
    "above_average": {"bg": "#84CC16", "text": "#FFFFFF", "icon": "⬆️", "label": "Above Average"},
    "average": {"bg": "#6B7280", "text": "#FFFFFF", "icon": "➖", "label": "Average"},
    "below_average": {"bg": "#F97316", "text": "#FFFFFF", "icon": "⬇️", "label": "Below Average"},
    "underperformer": {"bg": "#DC2626", "text": "#FFFFFF", "icon": "⚠️", "label": "Needs Attention"}
}

MEDAL_COLORS = {
    1: {"bg": "#FFD700", "icon": "🥇", "label": "Gold"},
    2: {"bg": "#C0C0C0", "icon": "🥈", "label": "Silver"},
    3: {"bg": "#CD7F32", "icon": "🥉", "label": "Bronze"}
}

METRIC_DISPLAY = {
    "dqi_score": {"name": "Data Quality Index", "icon": "📊", "unit": "score", "higher_is_better": True},
    "open_issues": {"name": "Open Issues", "icon": "🔴", "unit": "count", "higher_is_better": False},
    "missing_visits_pct": {"name": "Missing Visits", "icon": "📅", "unit": "%", "higher_is_better": False},
    "query_resolution_rate": {"name": "Query Resolution", "icon": "✅", "unit": "%", "higher_is_better": True},
    "sdv_completion_pct": {"name": "SDV Completion", "icon": "📋", "unit": "%", "higher_is_better": True},
    "enrollment_rate": {"name": "Enrollment Rate", "icon": "👥", "unit": "rate", "higher_is_better": True}
}


# ============ Pydantic Models ============

class UIBenchmarkMetric(BaseModel):
    name: str
    display_name: str
    value: float
    formatted_value: str
    percentile: float
    z_score: float
    performance: str
    performance_color: Dict[str, str]
    is_strength: bool
    is_weakness: bool
    bar_width: float


class UIBenchmarkResponse(BaseModel):
    site_id: str
    overall_percentile: float
    percentile_label: str
    overall_performance: str
    performance_color: Dict[str, str]
    study_rank: Optional[str]
    study_rank_display: str
    strengths: List[str]
    weaknesses: List[str]
    peer_insights: str
    recommendations: List[str]
    metrics: List[UIBenchmarkMetric]
    # Charts
    percentile_gauge: Dict[str, Any]
    metrics_radar: Dict[str, Any]
    peer_comparison: Dict[str, Any]


class UIRankingEntry(BaseModel):
    entity_id: str
    rank: int
    total: int
    value: float
    formatted_value: str
    percentile: float
    is_top_quartile: bool
    is_bottom_quartile: bool
    medal: Optional[Dict[str, str]]
    trend: str  # up, down, stable
    bar_width: float


class UIRankingResponse(BaseModel):
    metric: str
    metric_display: Dict[str, str]
    entity_type: str
    total_entities: int
    rankings: List[UIRankingEntry]
    top_performers: List[UIRankingEntry]
    bottom_performers: List[UIRankingEntry]
    # Chart data
    distribution_chart: Dict[str, Any]


class UILeaderboardEntry(BaseModel):
    entity_id: str
    overall_rank: int
    overall_score: float
    metric_ranks: Dict[str, int]
    medal: Optional[Dict[str, str]]
    performance_level: str
    performance_color: Dict[str, str]


class UILeaderboard(BaseModel):
    entity_type: str
    entries: List[UILeaderboardEntry]
    metrics: List[str]
    podium: List[Dict[str, Any]]  # Top 3


class UIAnalyticsDashboard(BaseModel):
    summary_stats: Dict[str, Any]
    risk_overview: Dict[str, Any]
    clustering_overview: Dict[str, Any]
    top_sites: List[Dict[str, Any]]
    bottom_sites: List[Dict[str, Any]]
    key_metrics: List[Dict[str, Any]]
    alerts_summary: Dict[str, Any]


# ============ Helper Functions ============

def get_performance_color(performance: str) -> Dict[str, str]:
    return PERFORMANCE_COLORS.get(performance, PERFORMANCE_COLORS["average"])

def format_metric_value(value: float, metric_name: str) -> str:
    info = METRIC_DISPLAY.get(metric_name, {})
    unit = info.get("unit", "")
    
    if unit == "%":
        return f"{value * 100:.1f}%"
    elif unit == "score":
        return f"{value:.1f}"
    elif unit == "count":
        return str(int(value))
    return f"{value:.2f}"

def get_percentile_label(percentile: float) -> str:
    if percentile >= 90:
        return "Excellent (Top 10%)"
    elif percentile >= 75:
        return "Good (Top 25%)"
    elif percentile >= 50:
        return "Average"
    elif percentile >= 25:
        return "Below Average"
    return "Needs Improvement"

def build_ranking_entry(r, metric_name: str) -> UIRankingEntry:
    medal = None
    if r.rank <= 3:
        medal = MEDAL_COLORS.get(r.rank)
    
    return UIRankingEntry(
        entity_id=r.entity_id,
        rank=r.rank,
        total=r.total,
        value=r.value,
        formatted_value=format_metric_value(r.value, metric_name),
        percentile=r.percentile,
        is_top_quartile=r.percentile >= 75,
        is_bottom_quartile=r.percentile <= 25,
        medal=medal,
        trend="stable",  # Would need historical data
        bar_width=min(r.percentile, 100)
    )


# ============ Engine Access ============

def get_engines():
    from api.main import _benchmark_engine, _ranking_engine
    if _benchmark_engine is None or _ranking_engine is None:
        raise HTTPException(status_code=500, detail="Analytics not initialized")
    return _benchmark_engine, _ranking_engine


# ============ UI-Ready Endpoints ============

@router.get("/dashboard")
async def get_analytics_dashboard():
    """
    Get unified analytics dashboard with all key metrics.
    
    Combines data from DQI, Risk, Clustering, and Rankings.
    """
    try:
        benchmark_engine, ranking_engine = get_engines()
        
        # Get leaderboard for summary
        leaderboard = ranking_engine.get_leaderboard("site", top_n=10)
        
        # Summary stats
        from analytics.rankings import RankingMetric
        dqi_ranking = ranking_engine.rank_sites(RankingMetric.DQI, limit=1000)
        
        total_sites = dqi_ranking.rankings[0].total if dqi_ranking.rankings else 0
        avg_dqi = sum(r.value for r in dqi_ranking.rankings) / len(dqi_ranking.rankings) if dqi_ranking.rankings else 0
        
        top_quartile = sum(1 for r in dqi_ranking.rankings if r.percentile >= 75)
        bottom_quartile = sum(1 for r in dqi_ranking.rankings if r.percentile <= 25)
        
        summary_stats = {
            "total_sites": total_sites,
            "average_dqi": round(avg_dqi, 1),
            "top_quartile_count": top_quartile,
            "bottom_quartile_count": bottom_quartile,
            "health_score": round(avg_dqi, 0),
            "health_label": "Good" if avg_dqi >= 70 else "Needs Attention" if avg_dqi >= 50 else "Critical",
            "health_color": "#22C55E" if avg_dqi >= 70 else "#F97316" if avg_dqi >= 50 else "#DC2626"
        }
        
        # Top and bottom sites
        top_sites = [
            {
                "entity_id": r.entity_id,
                "rank": r.rank,
                "value": round(r.value, 1),
                "percentile": round(r.percentile, 1),
                "medal": MEDAL_COLORS.get(r.rank)
            }
            for r in dqi_ranking.rankings[:5]
        ]
        
        bottom_sites = [
            {
                "entity_id": r.entity_id,
                "rank": r.rank,
                "value": round(r.value, 1),
                "percentile": round(r.percentile, 1)
            }
            for r in reversed(dqi_ranking.rankings[-5:])
        ]
        
        # Key metrics
        key_metrics = [
            {
                "name": "Average DQI",
                "value": round(avg_dqi, 1),
                "formatted": f"{avg_dqi:.1f}/100",
                "icon": "📊",
                "color": "#3B82F6"
            },
            {
                "name": "Sites Analyzed",
                "value": total_sites,
                "formatted": str(total_sites),
                "icon": "🏥",
                "color": "#8B5CF6"
            },
            {
                "name": "Top Performers",
                "value": top_quartile,
                "formatted": str(top_quartile),
                "icon": "🏆",
                "color": "#22C55E"
            },
            {
                "name": "Need Attention",
                "value": bottom_quartile,
                "formatted": str(bottom_quartile),
                "icon": "⚠️",
                "color": "#F97316"
            }
        ]
        
        # Risk overview placeholder
        risk_overview = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": total_sites
        }
        
        # Clustering overview placeholder
        clustering_overview = {
            "n_clusters": 0,
            "method": "pending"
        }
        
        # Alerts summary
        alerts_summary = {
            "total": bottom_quartile,
            "critical": 0,
            "high": bottom_quartile,
            "new_today": 0
        }
        
        return UIAnalyticsDashboard(
            summary_stats=summary_stats,
            risk_overview=risk_overview,
            clustering_overview=clustering_overview,
            top_sites=top_sites,
            bottom_sites=bottom_sites,
            key_metrics=key_metrics,
            alerts_summary=alerts_summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark/site/{site_id}", response_model=UIBenchmarkResponse)
async def benchmark_site_ui(site_id: str):
    """Get UI-ready comparative benchmark for a site."""
    try:
        benchmark_engine, _ = get_engines()
        result = benchmark_engine.benchmark_site(site_id)
        
        perf_color = get_performance_color(result.overall_performance.value)
        
        # Build metrics list
        metrics = []
        for m in result.metric_benchmarks:
            metric_perf = get_performance_color(m.performance_level.value)
            metrics.append(UIBenchmarkMetric(
                name=m.metric_name,
                display_name=m.metric_name.replace("_", " ").title(),
                value=m.entity_value,
                formatted_value=format_metric_value(m.entity_value, m.metric_name),
                percentile=m.percentile,
                z_score=m.z_score,
                performance=m.performance_level.value,
                performance_color=metric_perf,
                is_strength=m.percentile >= 75,
                is_weakness=m.percentile <= 25,
                bar_width=min(m.percentile, 100)
            ))
        
        # Percentile gauge
        percentile_gauge = {
            "type": "gauge",
            "value": result.overall_percentile,
            "max": 100,
            "color": perf_color["bg"],
            "zones": [
                {"min": 0, "max": 25, "color": "#DC2626"},
                {"min": 25, "max": 50, "color": "#F97316"},
                {"min": 50, "max": 75, "color": "#EAB308"},
                {"min": 75, "max": 100, "color": "#22C55E"}
            ]
        }
        
        # Metrics radar chart
        metrics_radar = {
            "type": "radar",
            "labels": [m.display_name[:10] for m in metrics[:6]],
            "data": [m.percentile for m in metrics[:6]],
            "color": "#3B82F6"
        }
        
        # Peer comparison
        peer_comparison = {
            "type": "comparison",
            "site_percentile": result.overall_percentile,
            "peer_average": 50,
            "top_performer": 95
        }
        
        return UIBenchmarkResponse(
            site_id=result.site_id,
            overall_percentile=result.overall_percentile,
            percentile_label=get_percentile_label(result.overall_percentile),
            overall_performance=result.overall_performance.value,
            performance_color=perf_color,
            study_rank=f"{result.study_rank}/{result.study_total}" if result.study_rank else None,
            study_rank_display=f"#{result.study_rank} of {result.study_total}" if result.study_rank else "N/A",
            strengths=result.strengths[:3],
            weaknesses=result.weaknesses[:3],
            peer_insights=result.peer_insights,
            recommendations=result.recommendations[:3],
            metrics=metrics,
            percentile_gauge=percentile_gauge,
            metrics_radar=metrics_radar,
            peer_comparison=peer_comparison
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/sites", response_model=UIRankingResponse)
async def rank_sites_ui(
    metric: str = Query("dqi_score", description="Metric to rank by"),
    study_id: Optional[str] = None,
    limit: int = Query(20, description="Number of results")
):
    """Get UI-ready site rankings by metric."""
    try:
        _, ranking_engine = get_engines()
        from analytics.rankings import RankingMetric
        
        metric_enum = None
        for m in RankingMetric:
            if m.value == metric:
                metric_enum = m
                break
        
        if not metric_enum:
            raise HTTPException(status_code=400, detail=f"Invalid metric: {metric}")
        
        result = ranking_engine.rank_sites(metric_enum, study_id=study_id, limit=limit)
        
        metric_info = METRIC_DISPLAY.get(metric, {"name": metric, "icon": "📈"})
        
        # Distribution chart
        distribution_chart = {
            "type": "histogram",
            "data": [
                {"range": "0-25", "count": sum(1 for r in result.rankings if r.percentile <= 25)},
                {"range": "25-50", "count": sum(1 for r in result.rankings if 25 < r.percentile <= 50)},
                {"range": "50-75", "count": sum(1 for r in result.rankings if 50 < r.percentile <= 75)},
                {"range": "75-100", "count": sum(1 for r in result.rankings if r.percentile > 75)}
            ]
        }
        
        return UIRankingResponse(
            metric=metric,
            metric_display=metric_info,
            entity_type=result.entity_type,
            total_entities=result.rankings[0].total if result.rankings else 0,
            rankings=[build_ranking_entry(r, metric) for r in result.rankings],
            top_performers=[build_ranking_entry(r, metric) for r in result.top_performers],
            bottom_performers=[build_ranking_entry(r, metric) for r in result.bottom_performers],
            distribution_chart=distribution_chart
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard", response_model=UILeaderboard)
async def get_leaderboard_ui(
    entity_type: str = Query("site", description="Entity type"),
    top_n: int = Query(10, description="Number of entries")
):
    """Get UI-ready leaderboard across all metrics."""
    try:
        _, ranking_engine = get_engines()
        raw_leaderboard = ranking_engine.get_leaderboard(entity_type, top_n)
        
        entries = []
        for i, entry in enumerate(raw_leaderboard):
            rank = i + 1
            medal = MEDAL_COLORS.get(rank) if rank <= 3 else None
            
            # Calculate average rank across metrics
            ranks = list(entry.get("ranks", {}).values())
            avg_rank = sum(ranks) / len(ranks) if ranks else 0
            
            perf_level = "top_performer" if avg_rank <= 5 else "above_average" if avg_rank <= 15 else "average"
            
            entries.append(UILeaderboardEntry(
                entity_id=entry.get("entity_id", f"Site {i}"),
                overall_rank=rank,
                overall_score=entry.get("avg_percentile", 50),
                metric_ranks=entry.get("ranks", {}),
                medal=medal,
                performance_level=perf_level,
                performance_color=get_performance_color(perf_level)
            ))
        
        # Podium (top 3)
        podium = [
            {
                "position": i + 1,
                "entity_id": entries[i].entity_id if i < len(entries) else None,
                "score": entries[i].overall_score if i < len(entries) else 0,
                "medal": MEDAL_COLORS.get(i + 1)
            }
            for i in range(3)
        ]
        
        return UILeaderboard(
            entity_type=entity_type,
            entries=entries,
            metrics=list(METRIC_DISPLAY.keys()),
            podium=podium
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
