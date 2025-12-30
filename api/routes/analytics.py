"""Analytics API - Benchmarking and ranking endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

router = APIRouter()


class BenchmarkResponse(BaseModel):
    site_id: str
    overall_percentile: float
    overall_performance: str
    study_rank: Optional[str] = None
    strengths: List[str] = []
    weaknesses: List[str] = []
    peer_insights: str = ""
    recommendations: List[str] = []


class RankingEntry(BaseModel):
    entity_id: str
    rank: int
    total: int
    value: float
    percentile: float


class RankingResponse(BaseModel):
    metric: str
    entity_type: str
    rankings: List[RankingEntry]
    top_performers: List[RankingEntry]
    bottom_performers: List[RankingEntry]


def get_engines():
    from api.main import _benchmark_engine, _ranking_engine
    if _benchmark_engine is None or _ranking_engine is None:
        raise HTTPException(status_code=500, detail="Analytics not initialized")
    return _benchmark_engine, _ranking_engine


@router.get("/benchmark/site/{site_id}", response_model=BenchmarkResponse)
async def benchmark_site(site_id: str):
    """Get comparative benchmark for a site."""
    try:
        benchmark_engine, _ = get_engines()
        result = benchmark_engine.benchmark_site(site_id)
        
        return BenchmarkResponse(
            site_id=result.site_id,
            overall_percentile=result.overall_percentile,
            overall_performance=result.overall_performance.value,
            study_rank=f"{result.study_rank}/{result.study_total}" if result.study_rank else None,
            strengths=result.strengths,
            weaknesses=result.weaknesses,
            peer_insights=result.peer_insights,
            recommendations=result.recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/sites", response_model=RankingResponse)
async def rank_sites(
    metric: str = "dqi_score",
    study_id: Optional[str] = None,
    limit: int = 20
):
    """Get site rankings by metric."""
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
        
        return RankingResponse(
            metric=result.metric.value,
            entity_type=result.entity_type,
            rankings=[
                RankingEntry(
                    entity_id=r.entity_id,
                    rank=r.rank,
                    total=r.total,
                    value=r.value,
                    percentile=r.percentile
                )
                for r in result.rankings
            ],
            top_performers=[
                RankingEntry(
                    entity_id=r.entity_id,
                    rank=r.rank,
                    total=r.total,
                    value=r.value,
                    percentile=r.percentile
                )
                for r in result.top_performers
            ],
            bottom_performers=[
                RankingEntry(
                    entity_id=r.entity_id,
                    rank=r.rank,
                    total=r.total,
                    value=r.value,
                    percentile=r.percentile
                )
                for r in result.bottom_performers
            ]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard")
async def get_leaderboard(entity_type: str = "site", top_n: int = 10):
    """Get leaderboard across all metrics."""
    try:
        _, ranking_engine = get_engines()
        return ranking_engine.get_leaderboard(entity_type, top_n)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
