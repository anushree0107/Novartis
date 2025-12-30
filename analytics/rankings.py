"""Ranking Engine - Site and patient rankings."""
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx


class RankingMetric(Enum):
    DQI = "dqi_score"
    OPEN_ISSUES = "open_issues"
    MISSING_VISITS = "missing_visits_pct"
    QUERY_RESOLUTION = "query_resolution_rate"
    SDV_COMPLETION = "sdv_completion_pct"
    ENROLLMENT = "enrollment_rate"


class RankingDirection(Enum):
    ASCENDING = "asc"
    DESCENDING = "desc"


@dataclass
class RankedEntity:
    """Entity with ranking information."""
    entity_id: str
    entity_type: str
    rank: int
    total: int
    value: float
    percentile: float
    
    metric_name: str
    direction: RankingDirection
    
    @property
    def is_top_quartile(self) -> bool:
        return self.percentile >= 75
    
    @property
    def is_bottom_quartile(self) -> bool:
        return self.percentile <= 25
    
    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "rank": self.rank,
            "total": self.total,
            "value": round(self.value, 3),
            "percentile": round(self.percentile, 1),
            "metric": self.metric_name,
            "top_quartile": self.is_top_quartile,
            "bottom_quartile": self.is_bottom_quartile
        }


@dataclass
class RankingResult:
    """Complete ranking result."""
    metric: RankingMetric
    entity_type: str
    direction: RankingDirection
    
    rankings: List[RankedEntity] = field(default_factory=list)
    
    top_performers: List[RankedEntity] = field(default_factory=list)
    bottom_performers: List[RankedEntity] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "metric": self.metric.value,
            "entity_type": self.entity_type,
            "direction": self.direction.value,
            "total_entities": len(self.rankings),
            "rankings": [r.to_dict() for r in self.rankings],
            "top_performers": [r.to_dict() for r in self.top_performers],
            "bottom_performers": [r.to_dict() for r in self.bottom_performers]
        }


class RankingEngine:
    """
    Ranking Engine for sites, patients, and studies.
    
    Features:
    - Multi-metric ranking
    - Configurable direction
    - Top/bottom performer identification
    - Percentile calculation
    """
    
    METRIC_DEFAULTS = {
        RankingMetric.DQI: RankingDirection.DESCENDING,
        RankingMetric.OPEN_ISSUES: RankingDirection.ASCENDING,
        RankingMetric.MISSING_VISITS: RankingDirection.ASCENDING,
        RankingMetric.QUERY_RESOLUTION: RankingDirection.DESCENDING,
        RankingMetric.SDV_COMPLETION: RankingDirection.DESCENDING,
        RankingMetric.ENROLLMENT: RankingDirection.DESCENDING,
    }
    
    def __init__(self, graph: nx.DiGraph, dqi_calculator=None):
        self.graph = graph
        self.dqi_calculator = dqi_calculator
    
    def rank_sites(
        self, 
        metric: RankingMetric = RankingMetric.DQI,
        direction: RankingDirection = None,
        study_id: Optional[str] = None,
        limit: int = None
    ) -> RankingResult:
        """Rank sites by a specific metric."""
        if direction is None:
            direction = self.METRIC_DEFAULTS.get(metric, RankingDirection.DESCENDING)
        
        if study_id:
            sites = self._get_study_sites(study_id)
        else:
            sites = self._get_all_sites()
        
        site_values = []
        for site in sites:
            value = self._get_metric_value(site, "site", metric)
            if value is not None:
                site_values.append((site, value))
        
        reverse = direction == RankingDirection.DESCENDING
        site_values.sort(key=lambda x: x[1], reverse=reverse)
        
        total = len(site_values)
        rankings = []
        
        for rank, (site_id, value) in enumerate(site_values, 1):
            if direction == RankingDirection.DESCENDING:
                percentile = ((total - rank + 1) / total) * 100
            else:
                percentile = ((total - rank + 1) / total) * 100
            
            rankings.append(RankedEntity(
                entity_id=site_id,
                entity_type="site",
                rank=rank,
                total=total,
                value=value,
                percentile=percentile,
                metric_name=metric.value,
                direction=direction
            ))
        
        if limit:
            rankings = rankings[:limit]
        
        top_count = max(1, total // 4)
        bottom_count = max(1, total // 4)
        
        return RankingResult(
            metric=metric,
            entity_type="site",
            direction=direction,
            rankings=rankings,
            top_performers=rankings[:top_count],
            bottom_performers=rankings[-bottom_count:] if len(rankings) > bottom_count else []
        )
    
    def rank_patients(
        self,
        metric: RankingMetric = RankingMetric.OPEN_ISSUES,
        direction: RankingDirection = None,
        site_id: Optional[str] = None,
        limit: int = 50
    ) -> RankingResult:
        """Rank patients by a specific metric."""
        if direction is None:
            direction = self.METRIC_DEFAULTS.get(metric, RankingDirection.ASCENDING)
        
        if site_id:
            patients = self._get_site_patients(site_id)
        else:
            patients = self._get_all_patients()[:500]
        
        patient_values = []
        for patient in patients:
            value = self._get_metric_value(patient, "patient", metric)
            if value is not None:
                patient_values.append((patient, value))
        
        reverse = direction == RankingDirection.DESCENDING
        patient_values.sort(key=lambda x: x[1], reverse=reverse)
        
        total = len(patient_values)
        rankings = []
        
        for rank, (patient_id, value) in enumerate(patient_values[:limit], 1):
            percentile = ((total - rank + 1) / total) * 100 if total > 0 else 50
            
            rankings.append(RankedEntity(
                entity_id=patient_id,
                entity_type="patient",
                rank=rank,
                total=total,
                value=value,
                percentile=percentile,
                metric_name=metric.value,
                direction=direction
            ))
        
        top_count = min(5, len(rankings))
        
        return RankingResult(
            metric=metric,
            entity_type="patient",
            direction=direction,
            rankings=rankings,
            top_performers=rankings[:top_count],
            bottom_performers=rankings[-top_count:] if len(rankings) > top_count else []
        )
    
    def get_leaderboard(self, entity_type: str = "site", top_n: int = 10) -> Dict[str, List[Dict]]:
        """Get leaderboard across multiple metrics."""
        leaderboard = {}
        
        for metric in RankingMetric:
            if entity_type == "site":
                result = self.rank_sites(metric, limit=top_n)
            else:
                result = self.rank_patients(metric, limit=top_n)
            
            leaderboard[metric.value] = [r.to_dict() for r in result.rankings]
        
        return leaderboard
    
    def _get_all_sites(self) -> List[str]:
        return [
            n.replace("SITE:", "")
            for n, d in self.graph.nodes(data=True)
            if d.get("node_type") == "Site"
        ]
    
    def _get_study_sites(self, study_id: str) -> List[str]:
        node_key = f"STUDY:{study_id}" if not study_id.startswith("STUDY:") else study_id
        
        if not self.graph.has_node(node_key):
            return []
        
        sites = []
        for neighbor in list(self.graph.successors(node_key)) + list(self.graph.predecessors(node_key)):
            if self.graph.nodes.get(neighbor, {}).get("node_type") == "Site":
                sites.append(neighbor.replace("SITE:", ""))
        
        return sites
    
    def _get_all_patients(self) -> List[str]:
        return [
            n.replace("SUBJECT:", "")
            for n, d in self.graph.nodes(data=True)
            if d.get("node_type") == "Subject"
        ]
    
    def _get_site_patients(self, site_id: str) -> List[str]:
        node_key = f"SITE:{site_id}" if not site_id.startswith("SITE:") else site_id
        
        if not self.graph.has_node(node_key):
            return []
        
        patients = []
        for neighbor in list(self.graph.successors(node_key)) + list(self.graph.predecessors(node_key)):
            if self.graph.nodes.get(neighbor, {}).get("node_type") == "Subject":
                patients.append(neighbor.replace("SUBJECT:", ""))
        
        return patients
    
    def _get_metric_value(self, entity_id: str, entity_type: str, metric: RankingMetric) -> Optional[float]:
        if entity_type == "site":
            node_key = f"SITE:{entity_id}" if not entity_id.startswith("SITE:") else entity_id
        else:
            node_key = f"SUBJECT:{entity_id}" if not entity_id.startswith("SUBJECT:") else entity_id
        
        if not self.graph.has_node(node_key):
            return None
        
        props = dict(self.graph.nodes[node_key])
        
        if metric == RankingMetric.DQI:
            if self.dqi_calculator and entity_type == "site":
                try:
                    result = self.dqi_calculator.calculate_site(entity_id.replace("SITE:", ""))
                    return result.score
                except Exception:
                    return 50.0
            return 50.0
        
        metric_map = {
            RankingMetric.OPEN_ISSUES: ["open_issues", "total_issues", "open_issue_count"],
            RankingMetric.MISSING_VISITS: ["missing_visits_pct", "missing_visits"],
            RankingMetric.QUERY_RESOLUTION: ["query_resolution_rate"],
            RankingMetric.SDV_COMPLETION: ["sdv_completion_pct", "sdv_pct"],
            RankingMetric.ENROLLMENT: ["enrollment_rate", "total_subjects"],
        }
        
        possible_keys = metric_map.get(metric, [])
        for key in possible_keys:
            if key in props:
                try:
                    return float(props[key])
                except (ValueError, TypeError):
                    continue
        
        return None
