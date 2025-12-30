"""Benchmark Engine - Comparative analysis across entities."""
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import networkx as nx


class PerformanceLevel(Enum):
    TOP_PERFORMER = "top_performer"
    ABOVE_AVERAGE = "above_average"
    AVERAGE = "average"
    BELOW_AVERAGE = "below_average"
    UNDERPERFORMER = "underperformer"


@dataclass
class MetricBenchmark:
    """Benchmark for a single metric."""
    metric_name: str
    entity_value: float
    cohort_mean: float
    cohort_median: float
    cohort_std: float
    cohort_min: float
    cohort_max: float
    percentile: float
    z_score: float
    performance_level: PerformanceLevel
    
    @property
    def is_strength(self) -> bool:
        return self.percentile >= 75
    
    @property
    def is_weakness(self) -> bool:
        return self.percentile <= 25
    
    def to_dict(self) -> Dict:
        return {
            "metric": self.metric_name,
            "value": round(self.entity_value, 3),
            "cohort_mean": round(self.cohort_mean, 3),
            "cohort_median": round(self.cohort_median, 3),
            "percentile": round(self.percentile, 1),
            "z_score": round(self.z_score, 2),
            "performance": self.performance_level.value,
            "is_strength": self.is_strength,
            "is_weakness": self.is_weakness
        }


@dataclass
class SiteBenchmark:
    """Complete benchmark result for a site."""
    site_id: str
    study_id: Optional[str] = None
    
    overall_percentile: float = 50.0
    overall_performance: PerformanceLevel = PerformanceLevel.AVERAGE
    
    regional_rank: Optional[int] = None
    regional_total: Optional[int] = None
    study_rank: Optional[int] = None
    study_total: Optional[int] = None
    global_rank: Optional[int] = None
    global_total: Optional[int] = None
    
    metric_benchmarks: List[MetricBenchmark] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    peer_insights: str = ""
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "site_id": self.site_id,
            "study_id": self.study_id,
            "overall_percentile": round(self.overall_percentile, 1),
            "overall_performance": self.overall_performance.value,
            "rankings": {
                "regional": f"{self.regional_rank}/{self.regional_total}" if self.regional_rank else None,
                "study": f"{self.study_rank}/{self.study_total}" if self.study_rank else None,
                "global": f"{self.global_rank}/{self.global_total}" if self.global_rank else None
            },
            "metrics": [m.to_dict() for m in self.metric_benchmarks],
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "peer_insights": self.peer_insights,
            "recommendations": self.recommendations
        }


@dataclass
class StudyBenchmark:
    """Benchmark result for a study."""
    study_id: str
    
    site_count: int = 0
    subject_count: int = 0
    
    avg_site_dqi: float = 0.0
    min_site_dqi: float = 0.0
    max_site_dqi: float = 0.0
    dqi_std: float = 0.0
    
    top_sites: List[Tuple[str, float]] = field(default_factory=list)
    bottom_sites: List[Tuple[str, float]] = field(default_factory=list)
    
    metric_summaries: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "study_id": self.study_id,
            "site_count": self.site_count,
            "subject_count": self.subject_count,
            "dqi_summary": {
                "mean": round(self.avg_site_dqi, 1),
                "min": round(self.min_site_dqi, 1),
                "max": round(self.max_site_dqi, 1),
                "std": round(self.dqi_std, 1)
            },
            "top_sites": [{"site": s, "dqi": round(d, 1)} for s, d in self.top_sites],
            "bottom_sites": [{"site": s, "dqi": round(d, 1)} for s, d in self.bottom_sites],
            "metrics": self.metric_summaries
        }


class BenchmarkEngine:
    """
    Enterprise Benchmark Engine for comparative analysis.
    
    Features:
    - Multi-level comparison (regional, study, global)
    - Percentile rankings
    - Z-score analysis
    - Strength/weakness identification
    - LLM-powered peer insights
    """
    
    BENCHMARK_METRICS = [
        "dqi_score",
        "open_issues",
        "missing_visits_pct",
        "query_resolution_rate",
        "sdv_completion_pct",
        "safety_review_rate",
        "enrollment_rate"
    ]
    
    def __init__(self, graph: nx.DiGraph, dqi_calculator=None, llm=None):
        self.graph = graph
        self.dqi_calculator = dqi_calculator
        self.llm = llm
        self._site_cache: Dict[str, Dict] = {}
        self._init_llm()
    
    def _init_llm(self):
        if self.llm is None:
            try:
                from langchain_groq import ChatGroq
                self.llm = ChatGroq(
                    model="llama-3.1-8b-instant",
                    temperature=0.3,
                    groq_api_key=os.getenv("GROQ_API_KEY")
                )
            except Exception:
                self.llm = None
    
    def benchmark_site(self, site_id: str, cohort: str = "study") -> SiteBenchmark:
        """Generate comprehensive benchmark for a site."""
        site_metrics = self._get_site_metrics(site_id)
        
        if cohort == "study":
            cohort_sites = self._get_study_cohort(site_id)
        elif cohort == "region":
            cohort_sites = self._get_regional_cohort(site_id)
        else:
            cohort_sites = self._get_global_cohort()
        
        cohort_metrics = [self._get_site_metrics(s) for s in cohort_sites if s != site_id]
        
        metric_benchmarks = []
        for metric in self.BENCHMARK_METRICS:
            if metric in site_metrics and cohort_metrics:
                cohort_values = [m.get(metric, 0) for m in cohort_metrics if metric in m]
                if cohort_values:
                    benchmark = self._compute_metric_benchmark(
                        metric,
                        site_metrics[metric],
                        cohort_values
                    )
                    metric_benchmarks.append(benchmark)
        
        overall_percentile = self._calculate_overall_percentile(metric_benchmarks)
        overall_performance = self._determine_performance_level(overall_percentile)
        
        strengths = [m.metric_name.replace("_", " ").title() 
                    for m in metric_benchmarks if m.is_strength]
        weaknesses = [m.metric_name.replace("_", " ").title() 
                     for m in metric_benchmarks if m.is_weakness]
        
        study_rank, study_total = self._calculate_rank(site_id, self._get_study_cohort(site_id))
        
        benchmark = SiteBenchmark(
            site_id=site_id,
            overall_percentile=overall_percentile,
            overall_performance=overall_performance,
            study_rank=study_rank,
            study_total=study_total,
            metric_benchmarks=metric_benchmarks,
            strengths=strengths,
            weaknesses=weaknesses
        )
        
        if self.llm:
            benchmark.peer_insights = self._generate_peer_insights(benchmark)
            benchmark.recommendations = self._generate_recommendations(benchmark)
        
        return benchmark
    
    def benchmark_study(self, study_id: str) -> StudyBenchmark:
        """Generate benchmark summary for an entire study."""
        sites = self._get_study_sites(study_id)
        
        site_dqi_scores = []
        for site in sites:
            metrics = self._get_site_metrics(site)
            if "dqi_score" in metrics:
                site_dqi_scores.append((site, metrics["dqi_score"]))
        
        site_dqi_scores.sort(key=lambda x: x[1], reverse=True)
        
        dqi_values = [s[1] for s in site_dqi_scores]
        
        subject_count = sum(
            len(self._get_related_nodes(f"SITE:{s}", "Subject"))
            for s in sites
        )
        
        metric_summaries = {}
        for metric in self.BENCHMARK_METRICS:
            values = []
            for site in sites:
                m = self._get_site_metrics(site)
                if metric in m:
                    values.append(m[metric])
            
            if values:
                metric_summaries[metric] = {
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "min": min(values),
                    "max": max(values)
                }
        
        return StudyBenchmark(
            study_id=study_id,
            site_count=len(sites),
            subject_count=subject_count,
            avg_site_dqi=statistics.mean(dqi_values) if dqi_values else 0,
            min_site_dqi=min(dqi_values) if dqi_values else 0,
            max_site_dqi=max(dqi_values) if dqi_values else 0,
            dqi_std=statistics.stdev(dqi_values) if len(dqi_values) > 1 else 0,
            top_sites=site_dqi_scores[:5],
            bottom_sites=site_dqi_scores[-5:] if len(site_dqi_scores) > 5 else [],
            metric_summaries=metric_summaries
        )
    
    def _get_site_metrics(self, site_id: str) -> Dict[str, float]:
        if site_id in self._site_cache:
            return self._site_cache[site_id]
        
        node_key = f"SITE:{site_id}" if not site_id.startswith("SITE:") else site_id
        clean_id = site_id.replace("SITE:", "")
        
        if not self.graph.has_node(node_key):
            return {}
        
        props = dict(self.graph.nodes[node_key])
        
        subjects = self._get_related_nodes(node_key, "Subject")
        total_subjects = len(subjects)
        
        dqi_score = 50.0
        if self.dqi_calculator:
            try:
                result = self.dqi_calculator.calculate_site(clean_id)
                dqi_score = result.score
            except Exception:
                pass
        
        metrics = {
            "dqi_score": dqi_score,
            "open_issues": int(props.get("open_issues", props.get("total_issues", 0))),
            "missing_visits_pct": float(props.get("missing_visits_pct", 0.05)),
            "query_resolution_rate": float(props.get("query_resolution_rate", 0.8)),
            "sdv_completion_pct": float(props.get("sdv_completion_pct", 0.85)),
            "safety_review_rate": float(props.get("safety_review_rate", 0.9)),
            "enrollment_rate": total_subjects / 50 if total_subjects > 0 else 0
        }
        
        self._site_cache[site_id] = metrics
        return metrics
    
    def _get_study_cohort(self, site_id: str) -> List[str]:
        node_key = f"SITE:{site_id}" if not site_id.startswith("SITE:") else site_id
        
        studies = self._get_related_nodes(node_key, "Study")
        if not studies:
            return self._get_global_cohort()[:50]
        
        study_sites = []
        for study in studies:
            sites = self._get_related_nodes(study, "Site")
            study_sites.extend([s.replace("SITE:", "") for s in sites])
        
        return list(set(study_sites))
    
    def _get_regional_cohort(self, site_id: str) -> List[str]:
        return self._get_study_cohort(site_id)
    
    def _get_global_cohort(self) -> List[str]:
        sites = [
            n.replace("SITE:", "") 
            for n, d in self.graph.nodes(data=True) 
            if d.get("node_type") == "Site"
        ]
        return sites[:100]
    
    def _get_study_sites(self, study_id: str) -> List[str]:
        node_key = f"STUDY:{study_id}" if not study_id.startswith("STUDY:") else study_id
        
        if not self.graph.has_node(node_key):
            return []
        
        sites = self._get_related_nodes(node_key, "Site")
        return [s.replace("SITE:", "") for s in sites]
    
    def _get_related_nodes(self, node_id: str, target_type: str) -> List[str]:
        if not self.graph.has_node(node_id):
            return []
        
        related = []
        for neighbor in list(self.graph.successors(node_id)) + list(self.graph.predecessors(node_id)):
            if self.graph.nodes.get(neighbor, {}).get("node_type") == target_type:
                related.append(neighbor)
        
        return related
    
    def _compute_metric_benchmark(
        self, 
        metric_name: str, 
        value: float, 
        cohort_values: List[float]
    ) -> MetricBenchmark:
        cohort_mean = statistics.mean(cohort_values)
        cohort_median = statistics.median(cohort_values)
        cohort_std = statistics.stdev(cohort_values) if len(cohort_values) > 1 else 0.01
        
        z_score = (value - cohort_mean) / cohort_std if cohort_std > 0 else 0
        
        sorted_values = sorted(cohort_values + [value])
        rank = sorted_values.index(value) + 1
        percentile = (rank / len(sorted_values)) * 100
        
        if metric_name in ["open_issues", "missing_visits_pct"]:
            percentile = 100 - percentile
            z_score = -z_score
        
        performance = self._determine_performance_level(percentile)
        
        return MetricBenchmark(
            metric_name=metric_name,
            entity_value=value,
            cohort_mean=cohort_mean,
            cohort_median=cohort_median,
            cohort_std=cohort_std,
            cohort_min=min(cohort_values),
            cohort_max=max(cohort_values),
            percentile=percentile,
            z_score=z_score,
            performance_level=performance
        )
    
    def _calculate_overall_percentile(self, benchmarks: List[MetricBenchmark]) -> float:
        if not benchmarks:
            return 50.0
        return statistics.mean([b.percentile for b in benchmarks])
    
    def _determine_performance_level(self, percentile: float) -> PerformanceLevel:
        if percentile >= 90:
            return PerformanceLevel.TOP_PERFORMER
        elif percentile >= 70:
            return PerformanceLevel.ABOVE_AVERAGE
        elif percentile >= 30:
            return PerformanceLevel.AVERAGE
        elif percentile >= 10:
            return PerformanceLevel.BELOW_AVERAGE
        else:
            return PerformanceLevel.UNDERPERFORMER
    
    def _calculate_rank(self, site_id: str, cohort: List[str]) -> Tuple[int, int]:
        site_metrics = self._get_site_metrics(site_id)
        dqi = site_metrics.get("dqi_score", 0)
        
        all_dqi = [(site_id, dqi)]
        for s in cohort:
            if s != site_id:
                m = self._get_site_metrics(s)
                all_dqi.append((s, m.get("dqi_score", 0)))
        
        all_dqi.sort(key=lambda x: x[1], reverse=True)
        rank = next((i+1 for i, (s, _) in enumerate(all_dqi) if s == site_id), len(all_dqi))
        
        return rank, len(all_dqi)
    
    def _generate_peer_insights(self, benchmark: SiteBenchmark) -> str:
        if not self.llm:
            return ""
        
        prompt = f"""Analyze this site's performance compared to peers and provide 2-3 sentences of insight:

Site: {benchmark.site_id}
Overall Percentile: {benchmark.overall_percentile:.0f}%
Performance Level: {benchmark.overall_performance.value}
Rank: {benchmark.study_rank}/{benchmark.study_total}

Strengths: {', '.join(benchmark.strengths) or 'None identified'}
Weaknesses: {', '.join(benchmark.weaknesses) or 'None identified'}

Provide actionable comparative insights for a CRA."""
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception:
            return ""
    
    def _generate_recommendations(self, benchmark: SiteBenchmark) -> List[str]:
        recommendations = []
        
        for metric in benchmark.metric_benchmarks:
            if metric.is_weakness:
                recommendations.append(
                    f"Focus on {metric.metric_name.replace('_', ' ')}: "
                    f"Currently at {metric.percentile:.0f}th percentile "
                    f"(value: {metric.entity_value:.2f} vs cohort avg: {metric.cohort_mean:.2f})"
                )
        
        if not recommendations:
            recommendations.append("Maintain current performance levels")
        
        return recommendations[:5]
