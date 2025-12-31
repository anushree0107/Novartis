"""DQI and Analytics Tools for Graph Agent."""
from typing import Optional, List, Dict, Type, Any
from pydantic import BaseModel, Field
import networkx as nx
import json

try:
    from ..core.base_tool import BaseTool
except ImportError:
    from core.base_tool import BaseTool

# --- Input Models ---

class CalculateDQIInput(BaseModel):
    entity_id: str = Field(description="Entity ID (e.g. 'Site 001', 'Study 21')")
    entity_type: str = Field(default="site", description="'site', 'study', or 'patient'")

class RankSitesInput(BaseModel):
    metric: str = Field(default="dqi_score", description="Metric: 'dqi_score', 'open_issues', 'missing_visits_pct'")
    limit: int = Field(default=10, description="Max results")
    direction: str = Field(default="desc", description="'asc' or 'desc'")
    study_id: Optional[str] = Field(default=None, description="Filter by study")

class BenchmarkSiteInput(BaseModel):
    site_id: str = Field(description="Site ID to benchmark")
    cohort: str = Field(default="study", description="'study', 'regional', or 'global'")

class PerformersInput(BaseModel):
    n: int = Field(default=10, description="Number of results")
    metric: str = Field(default="dqi_score", description="Metric to evaluate")

# --- Base Mixin ---

class DQIMixin:
    def __init__(self, graph: nx.DiGraph, llm=None, **kwargs):
        self.graph = graph
        self.llm = llm
        self._dqi_calculator = None
        self._explainer = None
        self._ranking_engine = None
        self._benchmark_engine = None
        super().__init__(**kwargs)

    @property
    def dqi_calculator(self):
        if not self._dqi_calculator and self.graph:
            from analytics.dqi.calculator import DQICalculator
            self._dqi_calculator = DQICalculator(self.graph)
        return self._dqi_calculator

    @property
    def explainer(self):
        if not self._explainer:
            from analytics.dqi.llm_validator import DQIValidator
            self._explainer = DQIValidator(self.llm)
        return self._explainer

    @property
    def ranking_engine(self):
        if not self._ranking_engine and self.graph:
            from analytics.rankings import RankingEngine
            self._ranking_engine = RankingEngine(self.graph, dqi_calculator=self.dqi_calculator)
        return self._ranking_engine

    @property
    def benchmark_engine(self):
        if not self._benchmark_engine and self.graph:
            from analytics.benchmarks import BenchmarkEngine
            self._benchmark_engine = BenchmarkEngine(self.graph, dqi_calculator=self.dqi_calculator, llm=self.llm)
        return self._benchmark_engine

# --- Tools ---

class CalculateDQITool(DQIMixin, BaseTool):
    name = "calculate_dqi"
    description = "Calculate Data Quality Index (DQI) score, grade, and issues for a site, study, or patient."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return CalculateDQIInput
    
    def _run(self, entity_id: str, entity_type: str = "site") -> str:
        try:
            if entity_type.lower() == "site":
                res = self.dqi_calculator.calculate_site(entity_id.replace("SITE:", ""))
            elif entity_type.lower() == "study":
                res = self.dqi_calculator.calculate_study(entity_id.replace("STUDY:", ""))
            else:
                res = self.dqi_calculator.calculate_patient(entity_id.replace("SUBJECT:", ""))
            
            warning = "\n(WARNING: SIMULATED DATA)" if getattr(res, 'is_default_data', False) else ""
            
            details = [f"- {m.name}: {m.raw_value:.2f} ({m.status})" for m in res.breakdown]
            
            return f"""DQI Result for {entity_type} {entity_id}:
Score: {res.score:.1f}/100
Grade: {res.grade}
Status: {res.status}
Top Issues: {', '.join(res.top_issues)}
Details:
{chr(10).join(details)}{warning}"""
        except Exception as e:
            return f"Error calculating DQI: {str(e)}"

class ExplainDQITool(DQIMixin, BaseTool):
    name = "explain_dqi"
    description = "Get an LLM-generated validation and analysis for a DQI score."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return CalculateDQIInput
    
    def _run(self, entity_id: str, entity_type: str = "site") -> str:
        try:
            if entity_type.lower() == "site":
                res = self.dqi_calculator.calculate_site(entity_id.replace("SITE:", ""))
            elif entity_type.lower() == "study":
                res = self.dqi_calculator.calculate_study(entity_id.replace("STUDY:", ""))
            else:
                res = self.dqi_calculator.calculate_patient(entity_id.replace("SUBJECT:", ""))
            
            # Use validate method from DQIValidator
            from analytics.dqi.weights import DQI_THRESHOLDS
            validation = self.explainer.validate(res, DQI_THRESHOLDS)
            
            return f"""Analysis for {entity_id}:
Score: {res.score:.1f}/100 | Grade: {res.grade} | Status: {res.status}

Validation:
{validation}"""
        except Exception as e:
            return f"Error explaining DQI: {str(e)}"

class RankSitesTool(DQIMixin, BaseTool):
    name = "rank_sites"
    description = "Rank sites by metrics (dqi_score, open_issues, missing_visits_pct)."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return RankSitesInput
    
    def _run(self, metric: str = "dqi_score", limit: int = 10, direction: str = "desc", study_id: str = None) -> str:
        try:
            # Map metric string to enum
            from analytics.rankings import RankingMetric, RankingDirection
            
            metric_map = {
                "dqi": RankingMetric.DQI, "dqi_score": RankingMetric.DQI,
                "issues": RankingMetric.OPEN_ISSUES, "open_issues": RankingMetric.OPEN_ISSUES,
                "missing": RankingMetric.MISSING_VISITS, "missing_visits_pct": RankingMetric.MISSING_VISITS
            }
            rmetric = metric_map.get(metric.lower(), RankingMetric.DQI)
            rdir = RankingDirection.ASCENDING if direction == "asc" else RankingDirection.DESCENDING
            
            res = self.ranking_engine.rank_sites(rmetric, rdir, study_id, limit)
            
            if res.insufficient_data:
                return "Insufficient data to rank sites."
            
            lines = [f"Rankings by {metric} ({direction}):"]
            for r in res.rankings:
                lines.append(f"{r.rank}. {r.entity_id}: {r.value:.2f}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error ranking sites: {str(e)}"

class BenchmarkSiteTool(DQIMixin, BaseTool):
    name = "benchmark_site"
    description = "Benchmark a site against its peers (study, regional, or global cohort)."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return BenchmarkSiteInput
    
    def _run(self, site_id: str, cohort: str = "study") -> str:
        try:
            res = self.benchmark_engine.benchmark_site(site_id, cohort)
            return f"""Benchmark for {res.site_id} (vs {cohort}):
Percentile: {res.overall_percentile:.1f}
Performance: {res.overall_performance}
Rank: {res.rank}/{res.cohort_size}
Strengths: {', '.join(res.strengths)}
Weaknesses: {', '.join(res.weaknesses)}
Insights: {res.peer_insights}"""
        except Exception as e:
            return f"Error benchmarking site: {str(e)}"

class IdentifyUnderperformersTool(DQIMixin, BaseTool):
    name = "identify_underperformers"
    description = "Identify underperforming sites needing attention."
    
    @property
    def args_schema(self) -> Type[BaseModel]:
        return PerformersInput
    
    def _run(self, n: int = 10, metric: str = "dqi_score") -> str:
        try:
            # Reusing rank_sites logic implicitly via tool loop or duplicating logic?
            # Creating wrapper logic
            # Underperformers: Low DQI (Asc), High Issues (Desc)
            direction = "asc" if metric in ["dqi_score", "dqi"] else "desc"
            
            from analytics.rankings import RankingMetric, RankingDirection
            # ... simple mapping ...
            metric_map = {"dqi_score": RankingMetric.DQI, "open_issues": RankingMetric.OPEN_ISSUES} 
            rmetric = metric_map.get(metric, RankingMetric.DQI)
            rdir = RankingDirection.ASCENDING if direction == "asc" else RankingDirection.DESCENDING
            
            res = self.ranking_engine.rank_sites(rmetric, rdir, limit=n)
            
            if res.insufficient_data:
                return "Insufficient data to identify underperformers."

            lines = [f"Underperformers ({metric}):"]
            for r in res.rankings:
                lines.append(f"- {r.entity_id}: {r.value:.2f}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"

def create_dqi_analytics_tools(graph: nx.DiGraph, llm=None) -> List[BaseTool]:
    """Create DQI and Analytics tools."""
    return [
        CalculateDQITool(graph=graph, llm=llm),
        ExplainDQITool(graph=graph, llm=llm),
        RankSitesTool(graph=graph, llm=llm),
        BenchmarkSiteTool(graph=graph, llm=llm),
        IdentifyUnderperformersTool(graph=graph, llm=llm)
    ]
